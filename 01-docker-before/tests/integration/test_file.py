from collections.abc import AsyncIterator, Callable

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient, Response

from erudio.core.config import Settings
from erudio.core.negotiation.media import MediaType
from erudio.main import create_app
from tests.conftest import BASE_URL, token_for
from tests.helpers import TIMESTAMP, assert_problem, parse

pytestmark = pytest.mark.integration

BASE = "/api/file/v1"
JSON, XML, YAML = MediaType.JSON.value, MediaType.XML.value, MediaType.YAML.value
MEDIA = [JSON, XML, YAML]


async def upload(
    client: AsyncClient, name: str, content: bytes, kind: str = "text/plain"
) -> Response:
    return await client.post(f"{BASE}/uploadFile", files={"file": (name, content, kind)})


@pytest.mark.parametrize("media", MEDIA)
async def test_upload_answers_in_every_media_type(
    client: AsyncClient, read_stored_file: Callable[[str], bytes], media: str
) -> None:
    response = await client.post(
        f"{BASE}/uploadFile",
        files={"file": ("golden.txt", b"golden file content\n", "text/plain")},
        headers={"Accept": media},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == media
    body = parse(response)
    assert list(body) == ["fileName", "fileDownloadUri", "fileType", "size"]
    assert body["fileName"] == "golden.txt"
    assert body["fileDownloadUri"] == f"{BASE_URL}{BASE}/downloadFile/golden.txt"
    assert body["fileType"] == "text/plain"
    assert int(body["size"]) == 20
    assert read_stored_file("golden.txt") == b"golden file content\n"


async def test_upload_overwrites_and_accepts_an_empty_file(
    client: AsyncClient, read_stored_file: Callable[[str], bytes]
) -> None:
    await upload(client, "same.txt", b"first")
    second = await client.post(
        f"{BASE}/uploadFile", files={"file": ("same.txt", b"", "text/plain")}
    )

    assert second.status_code == 200
    assert second.json()["size"] == 0
    assert read_stored_file("same.txt") == b""


async def test_upload_keeps_a_non_ascii_name_and_encodes_the_uri(
    client: AsyncClient, read_stored_file: Callable[[str], bytes]
) -> None:
    response = await client.post(
        f"{BASE}/uploadFile", files={"file": ("no ascii ção.txt", b"x", "text/plain")}
    )

    body = response.json()
    assert body["fileName"] == "no ascii ção.txt"
    assert body["fileDownloadUri"].endswith("/downloadFile/no%20ascii%20%C3%A7%C3%A3o.txt")
    assert read_stored_file("no ascii ção.txt") == b"x"
    downloaded = await client.get(body["fileDownloadUri"].removeprefix(BASE_URL))
    assert downloaded.content == b"x"


@pytest.mark.parametrize("media", MEDIA)
async def test_upload_multiple_files(
    client: AsyncClient, read_stored_file: Callable[[str], bytes], media: str
) -> None:
    response = await client.post(
        f"{BASE}/uploadMultipleFiles",
        files=[
            ("files", ("golden-a.txt", b"a", "text/plain")),
            ("files", ("golden-b.csv", b"a,b\n1,2\n", "text/csv")),
        ],
        headers={"Accept": media},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == media
    body = parse(response)
    items = body["item"] if media == XML else body
    assert [item["fileName"] for item in items] == ["golden-a.txt", "golden-b.csv"]
    assert [item["fileType"] for item in items] == ["text/plain", "text/csv"]
    assert [int(item["size"]) for item in items] == [1, 8]
    assert read_stored_file("golden-b.csv") == b"a,b\n1,2\n"


async def test_download_returns_the_file_as_an_attachment(client: AsyncClient) -> None:
    await upload(client, "download.csv", b"a,b\n", "text/csv")

    response = await client.get(f"{BASE}/downloadFile/download.csv")

    assert response.status_code == 200
    assert response.content == b"a,b\n"
    assert response.headers["content-type"].split(";")[0] == "text/csv"
    assert response.headers["content-disposition"] == 'attachment; filename="download.csv"'


async def test_download_of_an_unknown_type_is_octet_stream(client: AsyncClient) -> None:
    await upload(client, "blob.unknownext", b"\x00\x01")

    response = await client.get(f"{BASE}/downloadFile/blob.unknownext")

    assert response.headers["content-type"] == "application/octet-stream"


@pytest.mark.parametrize("media", MEDIA)
async def test_download_of_a_missing_file_is_a_404(client: AsyncClient, media: str) -> None:
    response = await client.get(
        f"{BASE}/downloadFile/does-not-exist.txt", headers={"Accept": media}
    )

    assert response.status_code == 404
    body = parse(response)
    assert list(body) == ["timestamp", "message", "details"]
    assert TIMESTAMP.match(body["timestamp"])
    assert body["message"] == "File not found does-not-exist.txt"
    assert body["details"] == "uri=/api/file/v1/downloadFile/does-not-exist.txt"


@pytest.mark.parametrize("name", ["..%2F..%2Fetc%2Fpasswd", "%2E%2E", "%2E", "..%5Csecret"])
async def test_download_rejects_traversal_style_names(client: AsyncClient, name: str) -> None:
    response = await client.get(f"{BASE}/downloadFile/{name}")

    assert response.status_code == 404


@pytest.mark.parametrize("name", ["../escaped.txt", "..\\escaped.txt", "a/b.txt", "..", "a..b.txt"])
async def test_upload_rejects_names_that_could_escape(client: AsyncClient, name: str) -> None:
    response = await upload(client, name, b"x")

    assert response.status_code == 400
    body = response.json()
    assert body["message"] == f"Could not store file {name}. Please try Again!"
    assert body["details"] == "uri=/api/file/v1/uploadFile"


async def test_upload_without_the_file_part_is_a_400(client: AsyncClient) -> None:
    response = await client.post(f"{BASE}/uploadFile", files={"other": ("a.txt", b"x")})

    body = await assert_problem(response, 400)
    assert {"in": "body", "field": "file", "message": "Field required"} in body["errors"]


async def test_upload_only_takes_multipart(client: AsyncClient) -> None:
    response = await client.post(f"{BASE}/uploadFile", json={"file": "x"})

    await assert_problem(response, 415, "Content-Type 'application/json' is not supported.")


async def test_upload_and_download_need_a_token(anonymous: AsyncClient) -> None:
    posted = await anonymous.post(f"{BASE}/uploadFile", files={"file": ("a.txt", b"x")})
    multiple = await anonymous.post(f"{BASE}/uploadMultipleFiles", files={"files": ("a.txt", b"x")})
    fetched = await anonymous.get(f"{BASE}/downloadFile/a.txt")

    for response in (posted, multiple, fetched):
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "token", ["garbage", token_for(secret="another-secret-with-32-bytes-or-more!!")]
)
async def test_an_invalid_token_is_rejected_before_the_upload_is_read(
    anonymous: AsyncClient, token: str
) -> None:
    response = await anonymous.post(
        f"{BASE}/uploadFile",
        files={"file": ("a.txt", b"x")},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


@pytest.fixture
def tiny_app(test_settings: Settings) -> FastAPI:
    return create_app(test_settings.model_copy(update={"max_request_size_mb": 0}))


async def test_a_body_over_the_request_limit_is_a_413(tiny_app: FastAPI) -> None:
    transport = ASGITransport(app=tiny_app, raise_app_exceptions=False)
    headers = {"Authorization": f"Bearer {token_for()}"}
    async with AsyncClient(transport=transport, base_url=BASE_URL, headers=headers) as http:
        response = await http.post(f"{BASE}/uploadFile", files={"file": ("a.txt", b"x")})

    await assert_problem(response, 413, "Maximum upload size exceeded")


async def test_a_streamed_body_over_the_limit_is_a_413(tiny_app: FastAPI) -> None:
    async def chunks() -> AsyncIterator[bytes]:
        yield b"--x\r\n"
        yield b"y" * 100

    transport = ASGITransport(app=tiny_app, raise_app_exceptions=False)
    headers = {
        "Authorization": f"Bearer {token_for()}",
        "Content-Type": "multipart/form-data; boundary=x",
    }
    async with AsyncClient(transport=transport, base_url=BASE_URL, headers=headers) as http:
        response = await http.post(f"{BASE}/uploadFile", content=chunks())

    await assert_problem(response, 413, "Maximum upload size exceeded")

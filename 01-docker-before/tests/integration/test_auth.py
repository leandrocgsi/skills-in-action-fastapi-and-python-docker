import json
import re
from datetime import datetime
from typing import Any

import jwt
import pytest
import yaml
from httpx import AsyncClient, Response

from erudio.core.negotiation.formats import parse_xml
from erudio.core.security import verify_password
from tests.conftest import SECRET, token_for

pytestmark = pytest.mark.integration

JSON, XML, YAML = "application/json", "application/xml", "application/yaml"
MEDIA = [JSON, XML, YAML]
TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")
LEANDRO = {"username": "leandro", "password": "admin123"}


def credentials(media: str, username: str, password: str, fullname: str | None = None) -> bytes:
    if media == XML:
        name = f"<fullname>{fullname}</fullname>" if fullname else ""
        return (
            f"<AccountCredentialsDTO><username>{username}</username>"
            f"<password>{password}</password>{name}</AccountCredentialsDTO>"
        ).encode()
    if media == YAML:
        extra = f"fullname: {fullname}\n" if fullname else ""
        return f"username: {username}\npassword: {password}\n{extra}".encode()
    body = {"username": username, "password": password}
    if fullname:
        body["fullname"] = fullname
    return json.dumps(body).encode()


def parse(response: Response) -> Any:
    kind = response.headers["content-type"].split(";")[0]
    if kind == XML:
        return parse_xml(response.content)
    if kind == YAML:
        return yaml.safe_load(response.content)
    return response.json()


async def post(client: AsyncClient, path: str, body: bytes, media: str = JSON) -> Response:
    return await client.post(path, content=body, headers={"Content-Type": media, "Accept": media})


async def sign_in(
    client: AsyncClient, username: str = "leandro", password: str = "admin123"
) -> Any:
    response = await post(client, "/auth/signin", credentials(JSON, username, password))
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.parametrize("media", MEDIA)
async def test_sign_in_returns_the_token_in_any_media_type(
    anonymous: AsyncClient, media: str
) -> None:
    response = await post(
        anonymous, "/auth/signin", credentials(media, "leandro", "admin123"), media
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == media
    token = parse(response)
    assert list(token) == [
        "username",
        "authenticated",
        "created",
        "expiration",
        "accessToken",
        "refreshToken",
    ]
    assert token["username"] == "leandro"
    assert str(token["authenticated"]).lower() == "true"
    assert TIMESTAMP.match(token["created"])
    assert TIMESTAMP.match(token["expiration"])
    created = datetime.fromisoformat(token["created"])
    assert (datetime.fromisoformat(token["expiration"]) - created).total_seconds() == 3600


async def test_the_tokens_carry_the_seeded_roles(anonymous: AsyncClient) -> None:
    token = await sign_in(anonymous)

    access = jwt.decode(token["accessToken"], SECRET, algorithms=["HS256"])
    refresh = jwt.decode(token["refreshToken"], SECRET, algorithms=["HS256"])
    assert access["roles"] == ["ADMIN", "MANAGER"]
    assert access["iss"] == "http://testserver"
    assert "iss" not in refresh


async def test_the_access_token_opens_the_api(anonymous: AsyncClient) -> None:
    token = await sign_in(anonymous)

    response = await anonymous.get(
        "/api/book/v1/1", headers={"Authorization": f"Bearer {token['accessToken']}"}
    )

    assert response.status_code == 200


@pytest.mark.parametrize("password", ["not-the-password", "ADMIN123", " admin123"])
async def test_a_wrong_password_is_a_401_bad_credentials(
    anonymous: AsyncClient, password: str
) -> None:
    response = await post(anonymous, "/auth/signin", credentials(JSON, "leandro", password))

    assert response.status_code == 401
    assert response.json()["message"] == "Bad credentials"
    assert response.json()["details"] == "uri=/auth/signin"
    assert "accessToken" not in response.text


async def test_an_unknown_user_looks_like_a_wrong_password(anonymous: AsyncClient) -> None:
    unknown = await post(anonymous, "/auth/signin", credentials(JSON, "nobody", "whatever"))
    wrong = await post(anonymous, "/auth/signin", credentials(JSON, "leandro", "whatever"))

    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json()["message"] == wrong.json()["message"] == "Bad credentials"


@pytest.mark.parametrize(
    "body",
    [
        {"username": "", "password": ""},
        {"username": "leandro", "password": ""},
        {"username": "   ", "password": "admin123"},
        {"username": "leandro"},
        {"password": "admin123"},
    ],
)
async def test_blank_or_missing_credentials_are_a_400(
    anonymous: AsyncClient, body: dict[str, str]
) -> None:
    response = await anonymous.post("/auth/signin", json=body)

    assert response.status_code == 400
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["title"] == "Bad Request"
    assert response.json()["errors"]


@pytest.mark.parametrize(("sent", "body"), [(JSON, b""), (JSON, b"{not json"), (XML, b"<a><b>")])
async def test_an_unreadable_body_is_a_400(anonymous: AsyncClient, sent: str, body: bytes) -> None:
    response = await anonymous.post("/auth/signin", content=body, headers={"Content-Type": sent})

    assert response.status_code == 400
    assert response.json()["detail"] == "Failed to read request"


async def test_a_bad_token_in_the_header_does_not_break_a_public_endpoint(
    anonymous: AsyncClient,
) -> None:
    response = await anonymous.post(
        "/auth/signin", json=LEANDRO, headers={"Authorization": "Bearer garbage"}
    )

    assert response.status_code == 200
    assert response.json()["accessToken"]


@pytest.mark.parametrize("media", MEDIA)
async def test_create_user_hashes_the_password_and_the_user_can_sign_in(
    anonymous: AsyncClient, media: str
) -> None:
    username = f"student-{media.split('/')[1]}"
    response = await post(
        anonymous, "/auth/createUser", credentials(media, username, "s3cret-pass", "Foo Bar"), media
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == media
    created = parse(response)
    assert list(created) == ["username", "password", "fullname"]
    assert created["username"] == username
    assert created["fullname"] == "Foo Bar"
    assert created["password"].startswith("$argon2id$")
    assert "s3cret-pass" not in created["password"]
    assert verify_password("s3cret-pass", created["password"])

    token = await sign_in(anonymous, username, "s3cret-pass")
    assert jwt.decode(token["accessToken"], SECRET, algorithms=["HS256"])["roles"] == []


async def test_create_user_without_a_full_name(anonymous: AsyncClient) -> None:
    response = await anonymous.post(
        "/auth/createUser", json={"username": "solo", "password": "p4ss"}
    )

    assert response.status_code == 200
    assert response.json()["fullname"] is None


async def test_a_repeated_username_is_a_409(anonymous: AsyncClient) -> None:
    first = await anonymous.post("/auth/createUser", json={"username": "twin", "password": "p4ss"})
    second = await anonymous.post(
        "/auth/createUser", json={"username": "twin", "password": "other"}
    )

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["message"] == "Username twin already exists!"
    assert (await anonymous.post("/auth/createUser", json=LEANDRO)).status_code == 409


@pytest.mark.parametrize(
    "body", [{"username": "x"}, {"password": "x"}, {"username": "", "password": "x"}]
)
async def test_create_user_needs_a_username_and_a_password(
    anonymous: AsyncClient, body: dict[str, str]
) -> None:
    assert (await anonymous.post("/auth/createUser", json=body)).status_code == 400


async def refresh(client: AsyncClient, username: str, authorization: str | None) -> Response:
    headers = {"Authorization": authorization} if authorization is not None else {}
    return await client.put(f"/auth/refresh/{username}", headers=headers)


async def test_refresh_returns_a_new_pair(anonymous: AsyncClient) -> None:
    token = await sign_in(anonymous)

    response = await refresh(anonymous, "leandro", f"Bearer {token['refreshToken']}")

    assert response.status_code == 200
    renewed = response.json()
    assert renewed["username"] == "leandro"
    assert jwt.decode(renewed["accessToken"], SECRET, algorithms=["HS256"])["sub"] == "leandro"
    xml = await anonymous.put(
        "/auth/refresh/leandro",
        headers={"Authorization": f"Bearer {token['refreshToken']}", "Accept": XML},
    )
    assert xml.headers["content-type"] == XML
    assert parse(xml)["username"] == "leandro"


async def test_refresh_rejects_bad_tokens_with_a_401(anonymous: AsyncClient) -> None:
    token = await sign_in(anonymous)
    cases = {
        "garbage": "Bearer not.a.token",
        "no bearer prefix": token["refreshToken"],
        "an access token": f"Bearer {token['accessToken']}",
        "another secret": f"Bearer {token_for(secret='another-secret-with-at-least-32-bytes')}",
    }

    for name, authorization in cases.items():
        response = await refresh(anonymous, "leandro", authorization)

        assert response.status_code == 401, name
        assert response.json()["message"] == "Expired or Invalid JWT Token!", name
        assert "accessToken" not in response.text


async def test_refresh_needs_the_authorization_header(anonymous: AsyncClient) -> None:
    response = await refresh(anonymous, "leandro", None)

    assert response.status_code == 400
    assert response.json()["errors"][0] == {
        "in": "header",
        "field": "authorization",
        "message": "Field required",
    }


async def test_refresh_of_an_unknown_user_is_a_404(anonymous: AsyncClient) -> None:
    token = await sign_in(anonymous)

    response = await refresh(anonymous, "nobody", f"Bearer {token['refreshToken']}")

    assert response.status_code == 404
    assert response.json()["message"] == "Username nobody not found!"


async def test_refresh_with_the_token_of_another_user_is_a_403(anonymous: AsyncClient) -> None:
    token = await sign_in(anonymous)

    response = await refresh(anonymous, "flavio", f"Bearer {token['refreshToken']}")

    assert response.status_code == 403
    assert response.json()["message"] == "The token does not belong to this user!"


async def test_a_refresh_token_does_not_open_the_api(anonymous: AsyncClient) -> None:
    token = await sign_in(anonymous)

    response = await anonymous.get(
        "/api/book/v1/1", headers={"Authorization": f"Bearer {token['refreshToken']}"}
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    "authorization",
    [
        None,
        "Bearer garbage",
        "Bearer ",
        "Basic bGVhbmRybzphZG1pbjEyMw==",
        "bearer-without-space",
    ],
)
async def test_the_api_answers_401_without_a_valid_token(
    anonymous: AsyncClient, authorization: str | None
) -> None:
    headers = {} if authorization is None else {"Authorization": authorization}

    response = await anonymous.get("/api/book/v1/1", headers=headers)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["title"] == "Unauthorized"
    assert "launchDate" not in response.text


async def test_expired_tokens_and_tokens_of_unknown_users_are_a_401(anonymous: AsyncClient) -> None:
    for token in (token_for(validity_ms=-60_000), token_for("ghost"), token_for(secret="x" * 40)):
        response = await anonymous.get("/api/book/v1", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 401


async def test_every_api_method_is_protected(anonymous: AsyncClient) -> None:
    calls = [
        anonymous.get("/api/book/v1"),
        anonymous.get("/api/book/v1/1"),
        anonymous.post("/api/book/v1", json={}),
        anonymous.put("/api/book/v1", json={}),
        anonymous.delete("/api/book/v1/1"),
    ]

    for call in calls:
        assert (await call).status_code == 401


async def test_the_documentation_and_the_auth_endpoints_stay_public(anonymous: AsyncClient) -> None:
    assert (await anonymous.get("/swagger-ui/index.html")).status_code == 200
    assert (await anonymous.get("/v3/api-docs")).status_code == 200
    assert (await anonymous.post("/auth/signin", json=LEANDRO)).status_code == 200


async def test_an_unknown_route_is_a_404_with_or_without_a_token(
    anonymous: AsyncClient, client: AsyncClient
) -> None:
    assert (await anonymous.get("/api/nothing/v1")).status_code == 404
    assert (await client.get("/api/nothing/v1")).status_code == 404


async def test_the_documentation_declares_the_bearer_scheme(anonymous: AsyncClient) -> None:
    document = (await anonymous.get("/v3/api-docs")).json()

    assert document["components"]["securitySchemes"]["Bearer"]["scheme"] == "bearer"
    assert document["paths"]["/api/book/v1"]["get"]["security"] == [{"Bearer": []}]
    assert "security" not in document["paths"]["/auth/signin"]["post"]

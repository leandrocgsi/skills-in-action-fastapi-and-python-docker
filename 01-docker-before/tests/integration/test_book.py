import json
from typing import Any

import pytest
from httpx import AsyncClient, Response

from erudio.core.negotiation.media import MediaType
from tests.helpers import TIMESTAMP, all_pages, assert_problem, parse

pytestmark = pytest.mark.integration

BASE = "/api/book/v1"
JSON, XML, YAML = MediaType.JSON.value, MediaType.XML.value, MediaType.YAML.value
MEDIA = [JSON, XML, YAML]

BOOK = {
    "author": "Nigel Poulton",
    "launchDate": "2024-01-01",
    "price": 55.99,
    "title": "Docker Deep Dive",
}
BODIES = {
    JSON: json.dumps(BOOK).encode(),
    XML: (
        b"<BookDTO><author>Nigel Poulton</author><launchDate>2024-01-01</launchDate>"
        b"<price>55.99</price><title>Docker Deep Dive</title></BookDTO>"
    ),
    YAML: b"author: Nigel Poulton\nlaunchDate: 2024-01-01\nprice: 55.99\ntitle: Docker Deep Dive\n",
}


def book_fields(data: dict[str, Any]) -> dict[str, Any]:
    fields = {key: data[key] for key in ("author", "launchDate", "price", "title")}
    fields["id"] = int(data["id"])
    fields["price"] = float(fields["price"])
    return fields


def items_of(media: str, data: dict[str, Any]) -> list[dict[str, Any]]:
    if media == JSON:
        return data["_embedded"]["books"]  # type: ignore[no-any-return]
    content = data["content"]
    if media == XML:
        content = content["content"] if isinstance(content, dict) else content
        content = content if isinstance(content, list) else [content]
    return content  # type: ignore[no-any-return]


async def post(client: AsyncClient, body: bytes, sent: str, accept: str) -> Response:
    return await client.post(BASE, content=body, headers={"Content-Type": sent, "Accept": accept})


@pytest.mark.parametrize("media", MEDIA)
async def test_find_all_first_page(client: AsyncClient, media: str) -> None:
    response = await client.get(BASE, params={"page": 0, "size": 5}, headers={"Accept": media})

    assert response.status_code == 200
    assert response.headers["content-type"] == media
    data = parse(response)
    assert len(items_of(media, data)) == 5
    page = data["page"]
    assert int(page["number"]) == 0
    assert int(page["size"]) == 5
    assert int(page["totalElements"]) == 215
    assert int(page["totalPages"]) == 43
    rels = list(data["_links"]) if media == JSON else [link["rel"] for link in data["links"]]
    assert rels == ["first", "self", "next", "last"]


@pytest.mark.parametrize("media", MEDIA)
async def test_find_by_id_returns_the_seeded_book(client: AsyncClient, media: str) -> None:
    response = await client.get(f"{BASE}/1", headers={"Accept": media})

    assert response.status_code == 200
    assert book_fields(parse(response)) == {
        "id": 1,
        "author": "Michael C. Feathers",
        "launchDate": "2017-11-29",
        "price": 49.0,
        "title": "Working effectively with legacy code",
    }


async def test_json_is_the_default_representation(client: AsyncClient) -> None:
    for headers in ({}, {"Accept": "*/*"}, {"Accept": "application/*"}):
        response = await client.get(f"{BASE}/1", headers=headers)
        assert response.headers["content-type"] == JSON


async def test_item_links(client: AsyncClient) -> None:
    links = (await client.get(f"{BASE}/7")).json()["_links"]

    assert list(links) == ["self", "findAll", "create", "update", "delete"]
    assert links["self"] == {"href": "http://testserver/api/book/v1/7", "type": "GET"}
    assert links["findAll"]["href"] == "http://testserver/api/book/v1?page=1&size=12&direction=asc"
    assert links["update"]["type"] == "PUT"
    assert links["delete"] == {"href": "http://testserver/api/book/v1/7", "type": "DELETE"}


@pytest.mark.parametrize("accept", MEDIA)
@pytest.mark.parametrize("sent", MEDIA)
async def test_create_reads_any_media_type_and_answers_in_any(
    client: AsyncClient, sent: str, accept: str
) -> None:
    response = await post(client, BODIES[sent], sent, accept)

    assert response.status_code == 200
    assert response.headers["content-type"] == accept
    created = book_fields(parse(response))
    assert created["id"] > 215
    assert {**created, "id": 0} == {**BOOK, "id": 0}


@pytest.mark.parametrize("media", MEDIA)
async def test_update_and_delete(client: AsyncClient, media: str) -> None:
    created = book_fields(parse(await post(client, BODIES[media], media, media)))

    changed = {**BOOK, "id": created["id"], "title": "Docker Deep Dive, 2nd"}
    updated = await client.put(BASE, json=changed, headers={"Accept": media})
    assert updated.status_code == 200
    assert book_fields(parse(updated))["title"] == "Docker Deep Dive, 2nd"

    fetched = await client.get(f"{BASE}/{created['id']}")
    assert fetched.json()["title"] == "Docker Deep Dive, 2nd"

    deleted = await client.delete(f"{BASE}/{created['id']}")
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert (await client.get(f"{BASE}/{created['id']}")).status_code == 404


async def test_round_trip_ignores_links_and_unknown_fields(client: AsyncClient) -> None:
    resource = (await client.get(f"{BASE}/1")).json()
    resource["title"] = "Changed"
    resource["nickname"] = "ignored"

    response = await client.put(BASE, json=resource)

    assert response.status_code == 200
    assert response.json()["title"] == "Changed"


async def test_post_ignores_the_id(client: AsyncClient) -> None:
    response = await client.post(BASE, json={**BOOK, "id": 1})

    assert response.status_code == 200
    assert response.json()["id"] != 1
    assert (await client.get(f"{BASE}/1")).json()["title"] == "Working effectively with legacy code"


async def test_a_title_longer_than_250_characters_is_accepted(client: AsyncClient) -> None:
    response = await client.post(BASE, json={**BOOK, "title": "t" * 400})

    assert response.status_code == 200
    assert len(response.json()["title"]) == 400


async def test_price_keeps_two_decimals(client: AsyncClient) -> None:
    response = await client.post(BASE, json={**BOOK, "price": 10.999})

    assert response.json()["price"] == 11.0


@pytest.mark.parametrize("media", MEDIA)
async def test_not_found_is_an_exception_response(client: AsyncClient, media: str) -> None:
    response = await client.get(f"{BASE}/999999", headers={"Accept": media})

    assert response.status_code == 404
    body = parse(response)
    assert list(body) == ["timestamp", "message", "details"]
    assert TIMESTAMP.match(body["timestamp"])
    assert body["message"] == "No records found for this ID!"
    assert body["details"] == "uri=/api/book/v1/999999"


async def test_update_and_delete_of_a_missing_book_are_404(client: AsyncClient) -> None:
    assert (await client.put(BASE, json={**BOOK, "id": 999999})).status_code == 404
    assert (await client.delete(f"{BASE}/999999")).status_code == 404


async def test_a_missing_field_is_a_400_with_the_field_errors(client: AsyncClient) -> None:
    payload = {key: value for key, value in BOOK.items() if key != "title"}

    body = await assert_problem(await client.post(BASE, json=payload), 400)

    assert body["title"] == "Bad Request"
    assert {"in": "body", "field": "title", "message": "Field required"} in body["errors"]


@pytest.mark.parametrize(
    "launch_date",
    ["2024-01-01T00:00:00.000+00:00", "2024-01-01T00:00:00Z", 1704067200000, "01/02/2024", ""],
)
async def test_only_a_plain_date_is_accepted(client: AsyncClient, launch_date: object) -> None:
    response = await client.post(BASE, json={**BOOK, "launchDate": launch_date})

    body = await assert_problem(response, 400)
    assert any(error["field"] == "launchDate" for error in body["errors"])


async def test_a_price_that_is_not_a_number_is_rejected(client: AsyncClient) -> None:
    await assert_problem(await client.post(BASE, json={**BOOK, "price": "abc"}), 400)


@pytest.mark.parametrize(
    ("sent", "body"),
    [(JSON, b"{not json"), (XML, b"<BookDTO><author>"), (YAML, b"a: [unclosed"), (JSON, b"null")],
)
async def test_a_malformed_body_is_a_400(client: AsyncClient, sent: str, body: bytes) -> None:
    response = await client.post(BASE, content=body, headers={"Content-Type": sent})

    await assert_problem(response, 400, "Failed to read request")


async def test_an_empty_body_is_a_400(client: AsyncClient) -> None:
    response = await client.post(BASE, headers={"Content-Type": JSON})

    await assert_problem(response, 400)


async def test_an_unsupported_content_type_is_a_415(client: AsyncClient) -> None:
    response = await client.post(BASE, content=b"x", headers={"Content-Type": "text/plain"})

    await assert_problem(response, 415, "Content-Type 'text/plain' is not supported.")


async def test_a_body_without_content_type_is_a_415(client: AsyncClient) -> None:
    response = await client.post(BASE, content=BODIES[JSON])

    await assert_problem(response, 415, "Content-Type 'None' is not supported.")


@pytest.mark.parametrize("accept", ["text/html", "application/pdf", "image/png, text/csv"])
async def test_an_unacceptable_accept_is_a_406(client: AsyncClient, accept: str) -> None:
    response = await client.get(f"{BASE}/1", headers={"Accept": accept})

    await assert_problem(
        response,
        406,
        "Acceptable representations: [application/json, application/xml, application/yaml].",
    )


async def test_method_not_allowed_lists_the_allowed_methods(client: AsyncClient) -> None:
    response = await client.patch(f"{BASE}/1")

    await assert_problem(response, 405, "Method 'PATCH' is not supported.")
    assert set(response.headers["allow"].split(", ")) == {"GET", "DELETE"}


async def test_unknown_routes_are_a_404_problem(client: AsyncClient) -> None:
    await assert_problem(
        await client.get("/api/nothing/v1"), 404, "No static resource api/nothing/v1."
    )


async def test_a_non_numeric_id_is_a_400(client: AsyncClient) -> None:
    body = await assert_problem(await client.get(f"{BASE}/abc"), 400)

    assert body["errors"][0]["in"] == "path"


@pytest.mark.parametrize(
    "params",
    [{"page": -1}, {"size": 0}, {"size": 13}, {"page": "abc"}, {"page": 2**31}, {"size": 2**40}],
)
async def test_invalid_pagination_is_a_400(client: AsyncClient, params: dict[str, Any]) -> None:
    await assert_problem(await client.get(BASE, params=params), 400)


async def test_pagination_beyond_the_last_page(client: AsyncClient) -> None:
    body = (await client.get(BASE, params={"page": 99999})).json()

    assert "_embedded" not in body
    assert list(body["_links"]) == ["first", "prev", "self", "last"]
    assert body["page"] == {"number": 99999, "size": 12, "totalElements": 215, "totalPages": 18}


async def test_direction_defaults_to_ascending_and_desc_reverses(client: AsyncClient) -> None:
    asc = (await client.get(BASE, params={"size": 3, "direction": "sideways"})).json()
    desc = (await client.get(BASE, params={"size": 3, "direction": "DESC"})).json()

    titles = [book["title"].lower() for book in asc["_embedded"]["books"]]
    assert titles == sorted(titles)
    assert asc["_links"]["self"]["href"].endswith("direction=asc")
    reversed_titles = [book["title"].lower() for book in desc["_embedded"]["books"]]
    assert reversed_titles == sorted(reversed_titles, reverse=True)
    assert desc["_links"]["self"]["href"].endswith("direction=desc")


async def test_ties_are_ordered_by_id(client: AsyncClient) -> None:
    asc = (await client.get(BASE, params={"size": 6})).json()["_embedded"]["books"]
    desc = await all_pages(client, BASE, "books", direction="desc")

    assert [book["id"] for book in asc] == [27, 63, 154, 179, 191, 208]
    group = [book["id"] for book in desc if book["title"].startswith("Agile and Iterative")]
    assert group == sorted(group, reverse=True)


async def test_documentation_lists_the_three_media_types(client: AsyncClient) -> None:
    document = (await client.get("/v3/api-docs")).json()

    assert document["openapi"].startswith("3.1")
    assert document["info"]["version"] == "v1"
    operation = document["paths"]["/api/book/v1/{book_id}"]["get"]
    assert set(operation["responses"]["200"]["content"]) == set(MEDIA)
    create = document["paths"]["/api/book/v1"]["post"]
    assert set(create["requestBody"]["content"]) == set(MEDIA)
    assert "422" not in create["responses"]
    assert create["responses"]["400"]["content"]["application/problem+json"]["schema"] == {
        "$ref": "#/components/schemas/ProblemDetail"
    }
    schemas = document["components"]["schemas"]
    assert {"BookResponse", "BookCreate", "BookUpdate", "ProblemDetail"} <= set(schemas)
    assert "HTTPValidationError" not in schemas
    assert schemas["BookResponse"]["properties"]["price"]["type"] == "number"


async def test_swagger_ui_is_served(client: AsyncClient) -> None:
    response = await client.get("/swagger-ui/index.html")

    assert response.status_code == 200
    assert "swagger" in response.text.lower()


async def test_cors_allows_the_configured_origins_only(client: AsyncClient) -> None:
    allowed = await client.get(f"{BASE}/1", headers={"Origin": "https://www.erudio.com.br"})
    blocked = await client.get(f"{BASE}/1", headers={"Origin": "https://evil.example"})

    assert allowed.headers["access-control-allow-origin"] == "https://www.erudio.com.br"
    assert allowed.headers["access-control-allow-credentials"] == "true"
    assert "access-control-allow-origin" not in blocked.headers
    assert blocked.status_code == 200

import io
import json
from collections.abc import Sequence
from typing import Any

import pytest
from httpx import AsyncClient, Response
from openpyxl import Workbook, load_workbook

from erudio.core.negotiation.media import MediaType
from tests.helpers import TIMESTAMP, all_pages, assert_problem, parse

pytestmark = pytest.mark.integration

BASE = "/api/person/v1"
ROOT = "http://testserver/api/person/v1"
JSON, XML, YAML = MediaType.JSON.value, MediaType.XML.value, MediaType.YAML.value
MEDIA = [JSON, XML, YAML]
CSV = "text/csv"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
TOTAL_PEOPLE = 209

PERSON = {
    "firstName": "Linus",
    "lastName": "Torvalds",
    "address": "Helsinki - Finland",
    "gender": "Male",
    "enabled": True,
    "profileUrl": "https://example.org/linus",
    "photoUrl": "https://example.org/linus.jpg",
}
BODIES = {
    JSON: json.dumps(PERSON).encode(),
    XML: (
        b"<PersonDTO><firstName>Linus</firstName><lastName>Torvalds</lastName>"
        b"<address>Helsinki - Finland</address><gender>Male</gender><enabled>true</enabled>"
        b"<profileUrl>https://example.org/linus</profileUrl>"
        b"<photoUrl>https://example.org/linus.jpg</photoUrl></PersonDTO>"
    ),
    YAML: (
        b"firstName: Linus\nlastName: Torvalds\naddress: Helsinki - Finland\ngender: Male\n"
        b"enabled: true\nprofileUrl: https://example.org/linus\n"
        b"photoUrl: https://example.org/linus.jpg\n"
    ),
}
LINK_RELS = [
    "findAll",
    "findByName",
    "self",
    "create",
    "massCreation",
    "update",
    "disable",
    "delete",
    "exportPage",
]


def as_list(value: Any) -> list[Any]:
    if value is None or value == "":
        return []
    return value if isinstance(value, list) else [value]


def people_of(media: str, data: dict[str, Any]) -> list[dict[str, Any]]:
    if media == JSON:
        return data["_embedded"]["people"]  # type: ignore[no-any-return]
    content = data["content"]
    return as_list(content["content"] if media == XML and isinstance(content, dict) else content)


def person_fields(data: dict[str, Any]) -> dict[str, Any]:
    fields = {key: data[key] for key in ("firstName", "lastName", "address", "gender")}
    fields["id"] = int(data["id"])
    fields["enabled"] = str(data["enabled"]).lower() == "true"
    return fields


def csv_file(*lines: str) -> bytes:
    return "\r\n".join(("first_name,last_name,address,gender", *lines, "")).encode()


def xlsx_file(*rows: Sequence[Any]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.append(["first_name", "last_name", "address", "gender"])
    for row in rows:
        sheet.append(list(row))
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


async def upload(client: AsyncClient, filename: str, content: bytes, **kwargs: Any) -> Response:
    return await client.post(f"{BASE}/massCreation", files={"file": (filename, content)}, **kwargs)


async def create(client: AsyncClient, **changes: Any) -> dict[str, Any]:
    response = await client.post(BASE, json={**PERSON, **changes})
    assert response.status_code == 200
    return response.json()  # type: ignore[no-any-return]


@pytest.mark.parametrize("media", MEDIA)
async def test_find_all_first_page(client: AsyncClient, media: str) -> None:
    response = await client.get(BASE, params={"page": 0, "size": 5}, headers={"Accept": media})

    assert response.status_code == 200
    assert response.headers["content-type"] == media
    data = parse(response)
    assert len(people_of(media, data)) == 5
    page = data["page"]
    assert [int(page[key]) for key in ("number", "size", "totalElements", "totalPages")] == [
        0,
        5,
        TOTAL_PEOPLE,
        42,
    ]


async def test_find_all_is_ordered_by_first_name_and_paged_links_are_correct(
    client: AsyncClient,
) -> None:
    body = (await client.get(BASE, params={"page": 1, "size": 10})).json()

    names = [person["firstName"] for person in body["_embedded"]["people"]]
    assert names == sorted(names, key=str.lower)
    assert list(body["_links"]) == ["first", "prev", "self", "next", "last"]
    assert body["_links"]["self"]["href"] == f"{ROOT}?page=1&size=10&direction=asc"
    assert body["_links"]["last"]["href"] == f"{ROOT}?page=20&size=10&direction=asc"


async def test_the_default_page_has_twelve_people(client: AsyncClient) -> None:
    body = (await client.get(BASE)).json()

    assert len(body["_embedded"]["people"]) == 12
    assert body["page"] == {
        "number": 0,
        "size": 12,
        "totalElements": TOTAL_PEOPLE,
        "totalPages": 18,
    }


async def test_direction_desc_reverses_the_order(client: AsyncClient) -> None:
    asc = await all_pages(client, BASE, "people")
    desc = await all_pages(client, BASE, "people", direction="DESC")
    last = (await client.get(BASE, params={"direction": "DESC"})).json()

    assert len(asc) == TOTAL_PEOPLE
    assert [p["id"] for p in desc] == [p["id"] for p in reversed(asc)]
    assert last["_links"]["self"]["href"].endswith("direction=desc")


async def test_pagination_beyond_the_last_page(client: AsyncClient) -> None:
    body = (await client.get(BASE, params={"page": 99999})).json()

    assert "_embedded" not in body
    assert body["page"]["totalElements"] == TOTAL_PEOPLE


@pytest.mark.parametrize(
    "params",
    [{"page": -1}, {"size": 0}, {"size": 13}, {"page": "abc"}, {"page": 2**31}, {"size": 2**40}],
)
async def test_invalid_pagination_is_a_400(client: AsyncClient, params: dict[str, Any]) -> None:
    await assert_problem(await client.get(BASE, params=params), 400)


@pytest.mark.parametrize("media", MEDIA)
async def test_find_by_id_returns_the_seeded_person(client: AsyncClient, media: str) -> None:
    response = await client.get(f"{BASE}/1", headers={"Accept": media})

    assert response.status_code == 200
    assert person_fields(parse(response)) == {
        "id": 1,
        "firstName": "Ayrton",
        "lastName": "Senna",
        "address": "São Paulo - Brasil",
        "gender": "Male",
        "enabled": True,
    }


async def test_item_links_are_the_nine_hypermedia_actions(client: AsyncClient) -> None:
    data = (await client.get(f"{BASE}/7")).json()
    links = data["_links"]

    assert list(links) == LINK_RELS
    assert links["self"] == {"href": f"{ROOT}/7", "type": "GET"}
    assert links["findAll"]["href"] == f"{ROOT}?page=1&size=12&direction=asc"
    assert links["findByName"]["href"] == f"{ROOT}/findPeopleByName/?page=1&size=12&direction=asc"
    assert links["massCreation"] == {"href": f"{ROOT}/massCreation", "type": "POST"}
    assert links["disable"] == {"href": f"{ROOT}/7", "type": "PATCH"}
    assert links["exportPage"] == {
        "href": f"{ROOT}/exportPage?page=1&size=12&direction=asc",
        "title": "Export People",
        "type": "GET",
    }
    assert {"profileUrl", "photoUrl"} <= set(data)


async def test_xml_and_yaml_carry_the_links_as_a_list(client: AsyncClient) -> None:
    for media in (XML, YAML):
        data = parse(await client.get(f"{BASE}/7", headers={"Accept": media}))
        assert [link["rel"] for link in data["links"]] == LINK_RELS


async def test_find_by_name_ignores_case_and_matches_anywhere(client: AsyncClient) -> None:
    response = await client.get(f"{BASE}/findPeopleByName/YRTON", params={"size": 5})

    body = response.json()
    assert [person["firstName"] for person in body["_embedded"]["people"]] == ["Ayrton"]
    assert body["_links"]["self"]["href"] == (
        f"{ROOT}/findPeopleByName/YRTON?page=0&size=5&direction=asc"
    )


@pytest.mark.parametrize("media", MEDIA)
async def test_find_by_name_in_every_media_type(client: AsyncClient, media: str) -> None:
    response = await client.get(f"{BASE}/findPeopleByName/ayrton", headers={"Accept": media})

    assert response.headers["content-type"] == media
    assert [p["firstName"] for p in people_of(media, parse(response))] == ["Ayrton"]


@pytest.mark.parametrize("term", ["%", "_", "zzzzzzzz"])
async def test_find_by_name_treats_wildcards_literally(client: AsyncClient, term: str) -> None:
    body = (await client.get(f"{BASE}/findPeopleByName/{term.replace('%', '%25')}")).json()

    assert body["page"] == {"number": 0, "size": 12, "totalElements": 0, "totalPages": 0}
    assert "_embedded" not in body


@pytest.mark.parametrize("accept", MEDIA)
@pytest.mark.parametrize("sent", MEDIA)
async def test_create_reads_any_media_type_and_answers_in_any(
    client: AsyncClient, sent: str, accept: str
) -> None:
    response = await client.post(
        BASE, content=BODIES[sent], headers={"Content-Type": sent, "Accept": accept}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == accept
    data = parse(response)
    created = person_fields(data)
    assert created["id"] > 212
    assert {**created, "id": 0} == {
        "id": 0,
        "firstName": "Linus",
        "lastName": "Torvalds",
        "address": "Helsinki - Finland",
        "gender": "Male",
        "enabled": True,
    }
    assert data["profileUrl"] == "https://example.org/linus"


async def test_post_ignores_the_id_and_the_links(client: AsyncClient) -> None:
    resource = {**PERSON, "id": 1, "_links": {"self": {"href": "x"}}, "nickname": "ignored"}

    response = await client.post(BASE, json=resource)

    assert response.status_code == 200
    assert response.json()["id"] != 1
    assert (await client.get(f"{BASE}/1")).json()["firstName"] == "Ayrton"


@pytest.mark.parametrize("field", ["firstName", "lastName", "address", "gender", "enabled"])
async def test_every_required_field_is_validated(client: AsyncClient, field: str) -> None:
    payload = {key: value for key, value in PERSON.items() if key != field}

    body = await assert_problem(await client.post(BASE, json=payload), 400)

    assert {"in": "body", "field": field, "message": "Field required"} in body["errors"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("firstName", "f" * 81),
        ("lastName", "l" * 81),
        ("address", "a" * 101),
        ("gender", "Female!"),
    ],
)
async def test_values_longer_than_the_columns_are_a_400(
    client: AsyncClient, field: str, value: str
) -> None:
    body = await assert_problem(await client.post(BASE, json={**PERSON, field: value}), 400)

    assert any(error["field"] == field for error in body["errors"])


async def test_optional_urls_may_be_missing(client: AsyncClient) -> None:
    payload = {key: value for key, value in PERSON.items() if not key.endswith("Url")}

    body = (await client.post(BASE, json=payload)).json()

    assert body["profileUrl"] is None
    assert body["photoUrl"] is None


async def test_an_enabled_that_is_not_a_boolean_is_a_400(client: AsyncClient) -> None:
    await assert_problem(await client.post(BASE, json={**PERSON, "enabled": "maybe"}), 400)


async def test_a_json_null_body_is_a_400(client: AsyncClient) -> None:
    response = await client.post(BASE, content=b"null", headers={"Content-Type": JSON})

    await assert_problem(response, 400, "Failed to read request")


async def test_update_changes_only_the_four_fields(client: AsyncClient) -> None:
    person = await create(client)

    response = await client.put(
        BASE,
        json={
            "id": person["id"],
            "firstName": "Linus B.",
            "lastName": "T.",
            "address": "Portland",
            "gender": "Male",
            "enabled": False,
            "photoUrl": "http://changed",
        },
    )

    assert response.status_code == 200
    updated = response.json()
    assert (updated["firstName"], updated["lastName"], updated["address"]) == (
        "Linus B.",
        "T.",
        "Portland",
    )
    assert updated["enabled"] is True
    assert updated["photoUrl"] == PERSON["photoUrl"]
    assert updated["profileUrl"] == PERSON["profileUrl"]


async def test_round_trip_of_a_whole_resource_with_links(client: AsyncClient) -> None:
    resource = (await client.get(f"{BASE}/2")).json()
    resource["address"] = "Somewhere else"

    response = await client.put(BASE, json=resource)

    assert response.status_code == 200
    assert response.json()["address"] == "Somewhere else"


@pytest.mark.parametrize("media", MEDIA)
async def test_update_in_every_media_type(client: AsyncClient, media: str) -> None:
    person = await create(client)
    changed = {**person, "address": "Portland - USA"}
    body = {
        JSON: json.dumps(changed).encode(),
        XML: (
            f"<PersonDTO><id>{person['id']}</id><firstName>Linus</firstName>"
            "<lastName>Torvalds</lastName><address>Portland - USA</address>"
            "<gender>Male</gender></PersonDTO>"
        ).encode(),
        YAML: (
            f"id: {person['id']}\nfirstName: Linus\nlastName: Torvalds\n"
            "address: Portland - USA\ngender: Male\n"
        ).encode(),
    }[media]

    response = await client.put(
        BASE, content=body, headers={"Content-Type": media, "Accept": media}
    )

    assert response.status_code == 200
    assert parse(response)["address"] == "Portland - USA"


async def test_update_needs_an_existing_id(client: AsyncClient) -> None:
    payload = {key: PERSON[key] for key in ("firstName", "lastName", "address", "gender")}

    assert (await client.put(BASE, json={**payload, "id": 999999})).status_code == 404
    body = await assert_problem(await client.put(BASE, json=payload), 400)
    assert {"in": "body", "field": "id", "message": "Field required"} in body["errors"]


async def test_update_requires_the_last_name(client: AsyncClient) -> None:
    person = await create(client)
    payload = {"id": person["id"], "firstName": "A", "address": "B", "gender": "Male"}

    await assert_problem(await client.put(BASE, json=payload), 400)


@pytest.mark.parametrize("media", MEDIA)
async def test_disable_keeps_the_other_fields(client: AsyncClient, media: str) -> None:
    person = await create(client)

    response = await client.patch(f"{BASE}/{person['id']}", headers={"Accept": media})

    assert response.status_code == 200
    data = parse(response)
    assert str(data["enabled"]).lower() == "false"
    assert data["firstName"] == "Linus"
    assert (await client.get(f"{BASE}/{person['id']}")).json()["enabled"] is False


async def test_delete_removes_the_person(client: AsyncClient) -> None:
    person = await create(client)

    deleted = await client.delete(f"{BASE}/{person['id']}")

    assert deleted.status_code == 204
    assert deleted.content == b""
    assert (await client.get(f"{BASE}/{person['id']}")).status_code == 404
    assert (await client.delete(f"{BASE}/{person['id']}")).status_code == 404


async def test_deleting_a_person_removes_the_books_link_rows(client: AsyncClient) -> None:
    assert (await client.delete(f"{BASE}/1")).status_code == 204
    assert (await client.get(f"{BASE}/1")).status_code == 404
    assert (await client.get("/api/book/v1/1")).status_code == 200


@pytest.mark.parametrize("media", MEDIA)
async def test_not_found_is_an_exception_response(client: AsyncClient, media: str) -> None:
    response = await client.get(f"{BASE}/999999", headers={"Accept": media})

    assert response.status_code == 404
    body = parse(response)
    assert list(body) == ["timestamp", "message", "details"]
    assert TIMESTAMP.match(body["timestamp"])
    assert body["message"] == "No records found for this ID!"
    assert body["details"] == "uri=/api/person/v1/999999"


async def test_disable_of_a_missing_person_is_404(client: AsyncClient) -> None:
    assert (await client.patch(f"{BASE}/999999")).status_code == 404


async def test_every_route_requires_a_token(anonymous: AsyncClient) -> None:
    calls = [
        anonymous.get(BASE),
        anonymous.get(f"{BASE}/1"),
        anonymous.get(f"{BASE}/findPeopleByName/a"),
        anonymous.get(f"{BASE}/exportPage", headers={"Accept": CSV}),
        anonymous.post(BASE, json=PERSON),
        anonymous.post(f"{BASE}/massCreation", files={"file": ("a.csv", csv_file())}),
        anonymous.put(BASE, json={"id": 1}),
        anonymous.patch(f"{BASE}/1"),
        anonymous.delete(f"{BASE}/1"),
    ]

    for call in calls:
        response = await call
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("media", MEDIA)
async def test_mass_creation_from_csv(client: AsyncClient, media: str) -> None:
    content = csv_file("PostmanCsvA,Csv,Street 1,Female", 'PostmanCsvB,Csv,"Street 2, apto 3",Male')

    response = await upload(client, "people.csv", content, headers={"Accept": media})

    assert response.status_code == 200
    assert response.headers["content-type"] == media
    data = parse(response)
    created = as_list(data["item"]) if media == XML else data
    assert [person["firstName"] for person in created] == ["PostmanCsvA", "PostmanCsvB"]
    assert created[1]["address"] == "Street 2, apto 3"
    assert all(str(person["enabled"]).lower() == "true" for person in created)
    assert [link["rel"] for link in as_list(created[0].get("links", created[0].get("_links")))] == (
        LINK_RELS
    )
    total = (await client.get(BASE)).json()["page"]["totalElements"]
    assert total == TOTAL_PEOPLE + 2


async def test_mass_creation_items_are_plain_json_with_a_links_list(client: AsyncClient) -> None:
    created = (await upload(client, "people.csv", csv_file("A,B,C,Male"))).json()

    assert isinstance(created, list)
    assert [link["rel"] for link in created[0]["links"]] == LINK_RELS
    assert "_links" not in created[0]


async def test_mass_creation_from_xlsx(client: AsyncClient) -> None:
    content = xlsx_file(("Sheet", "One", "Row 1", "Male"), ("Sheet", "Two", "Row 2", "Female"))

    response = await upload(client, "people.xlsx", content)

    assert response.status_code == 200
    assert [person["lastName"] for person in response.json()] == ["One", "Two"]


async def test_mass_creation_ignores_blank_lines_and_trims_values(client: AsyncClient) -> None:
    content = csv_file("  Trim ,  Me , Here ,Male", ",,,", "")

    created = (await upload(client, "people.csv", content)).json()

    assert [(p["firstName"], p["lastName"], p["address"]) for p in created] == [
        ("Trim", "Me", "Here")
    ]


async def test_mass_creation_reads_a_csv_with_bom(client: AsyncClient) -> None:
    content = b"\xef\xbb\xbf" + csv_file("Bom,Test,Street,Male")

    assert (await upload(client, "people.csv", content)).status_code == 200


@pytest.mark.parametrize(
    ("filename", "content", "message"),
    [
        ("people.csv", b"", "Please set a Valid File!"),
        ("people.txt", b"first_name\nA", "Invalid File Format!"),
        ("people", csv_file("A,B,C,Male"), "Invalid File Format!"),
        ("people.csv", b"first_name,last_name\nA,B\n", "Error processing the file!"),
        (
            "people.csv",
            b"first_name,last_name,address,gender\nA,\xff,C,D\n",
            "Error processing the file!",
        ),
        ("people.csv", csv_file("A,B"), "Error processing the file!"),
        ("people.xlsx", b"this is not a workbook", "Error processing the file!"),
    ],
)
async def test_mass_creation_rejects_bad_files(
    client: AsyncClient, filename: str, content: bytes, message: str
) -> None:
    response = await upload(client, filename, content)

    assert response.status_code == 400
    assert response.json()["message"] == message
    assert response.json()["details"] == "uri=/api/person/v1/massCreation"


async def test_a_bad_row_rolls_back_the_whole_file(client: AsyncClient) -> None:
    content = csv_file("Good,Row,Street,Male", f"Bad,Row,{'x' * 101},Male")

    response = await upload(client, "people.csv", content)

    assert response.status_code == 400
    assert (await client.get(BASE)).json()["page"]["totalElements"] == TOTAL_PEOPLE


async def test_mass_creation_needs_the_file_part(client: AsyncClient) -> None:
    other = await client.post(f"{BASE}/massCreation", files={"attachment": ("a.csv", b"x")})

    body = await assert_problem(other, 400)
    assert {"in": "body", "field": "file", "message": "Field required"} in body["errors"]


async def test_mass_creation_only_takes_multipart(client: AsyncClient) -> None:
    response = await client.post(f"{BASE}/massCreation", json={})

    await assert_problem(response, 415, "Content-Type 'application/json' is not supported.")


async def test_export_csv(client: AsyncClient) -> None:
    response = await client.get(
        f"{BASE}/exportPage", params={"page": 0, "size": 5}, headers={"Accept": CSV}
    )

    assert response.status_code == 200
    assert response.headers["content-type"].split(";")[0] == CSV
    assert response.headers["content-disposition"] == 'attachment; filename="people_exported.csv"'
    lines = response.text.split("\r\n")
    assert lines[0] == "ID,First Name,Last Name,Address,Gender,Enabled"
    assert len(lines) == 7
    assert lines[-1] == ""
    first = lines[1].split(",")
    assert first[1] == min(person[1] for person in (line.split(",") for line in lines[1:-1]))
    assert first[-1] in {"true", "false"}


async def test_export_xlsx(client: AsyncClient) -> None:
    response = await client.get(
        f"{BASE}/exportPage", params={"page": 1, "size": 7}, headers={"Accept": XLSX}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == XLSX
    assert response.headers["content-disposition"] == 'attachment; filename="people_exported.xlsx"'
    sheet = load_workbook(io.BytesIO(response.content)).active
    assert sheet is not None
    assert sheet.title == "People"
    rows = list(sheet.values)
    assert rows[0] == ("ID", "First Name", "Last Name", "Address", "Gender", "Enabled")
    assert len(rows) == 8
    assert {row[5] for row in rows[1:]} <= {"Yes", "No"}


async def test_export_and_import_round_trip(client: AsyncClient) -> None:
    exported = await client.get(
        f"{BASE}/exportPage", params={"size": 4, "direction": "desc"}, headers={"Accept": XLSX}
    )
    sheet = load_workbook(io.BytesIO(exported.content)).active
    assert sheet is not None
    rows = [row[1:5] for row in list(sheet.values)[1:]]

    imported = await upload(client, "again.xlsx", xlsx_file(*rows))

    assert [
        (p["firstName"], p["lastName"], p["address"], p["gender"]) for p in imported.json()
    ] == rows


@pytest.mark.parametrize("accept", ["application/pdf", "text/html", "application/json"])
async def test_export_of_other_formats_is_a_406(client: AsyncClient, accept: str) -> None:
    response = await client.get(f"{BASE}/exportPage", headers={"Accept": accept})

    await assert_problem(response, 406, f"Acceptable representations: [{CSV}, {XLSX}].")


async def test_export_prefers_the_higher_quality_format(client: AsyncClient) -> None:
    response = await client.get(
        f"{BASE}/exportPage", headers={"Accept": f"{CSV};q=0.2, {XLSX};q=0.9"}
    )

    assert response.headers["content-type"] == XLSX


async def test_export_without_accept_defaults_to_csv(client: AsyncClient) -> None:
    for headers in ({}, {"Accept": "*/*"}):
        response = await client.get(f"{BASE}/exportPage", headers=headers)
        assert response.headers["content-type"].split(";")[0] == CSV


async def test_the_pdf_route_is_not_registered(client: AsyncClient) -> None:
    await assert_problem(
        await client.get(f"{BASE}/export/1"), 404, "No static resource api/person/v1/export/1."
    )


async def test_a_non_numeric_id_is_a_400(client: AsyncClient) -> None:
    body = await assert_problem(await client.get(f"{BASE}/abc"), 400)

    assert body["errors"][0]["in"] == "path"

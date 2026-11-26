import json

import pytest
import yaml
from starlette.datastructures import URL

from erudio.core.errors import MalformedBodyError
from erudio.core.hypermedia.models import Link, Page, PageInfo, Plain, Resource, ResourceList
from erudio.core.hypermedia.pagination import page_info, page_links
from erudio.core.negotiation.formats import parse_xml, parse_yaml, render, to_json_body
from erudio.core.negotiation.media import MediaType

BOOK = Resource(
    "BookDTO",
    {"id": 1, "author": "Ana", "title": "São Paulo", "price": 49.0, "note": None, "ok": True},
    [Link("self", "http://h/1", "GET"), Link("export", "http://h/x", "GET", "Export")],
)
BASE = URL("http://h/api/book/v1")


def test_json_item_is_hal_with_links_first() -> None:
    body = json.loads(render(MediaType.JSON, BOOK))
    assert next(iter(body)) == "_links"
    assert body["_links"]["self"] == {"href": "http://h/1", "type": "GET"}
    assert body["_links"]["export"] == {"href": "http://h/x", "title": "Export", "type": "GET"}
    assert body["price"] == 49.0
    assert body["note"] is None


def test_json_uses_compact_separators_and_keeps_unicode() -> None:
    raw = render(MediaType.JSON, BOOK).decode()
    assert '"title":"São Paulo"' in raw
    assert ": " not in raw


def test_xml_item_has_links_list_and_xsi_nil() -> None:
    raw = render(MediaType.XML, BOOK).decode()
    assert raw.startswith("<BookDTO xmlns:xsi=")
    assert "<links><rel>self</rel><href>http://h/1</href><type>GET</type></links>" in raw
    assert (
        "<links><rel>export</rel><href>http://h/x</href><title>Export</title><type>GET</type></links>"
        in raw
    )
    assert 'xsi:nil="true"' in raw
    assert "<ok>true</ok>" in raw
    assert "<price>49.0</price>" in raw


def test_yaml_item_quotes_values_but_not_keys() -> None:
    raw = render(MediaType.YAML, BOOK).decode()
    assert raw.startswith("---\n")
    assert 'title: "São Paulo"' in raw
    assert "note: null" in raw
    assert 'links:\n- rel: "self"' in raw
    assert yaml.safe_load(raw)["price"] == 49.0


def make_page(count: int, number: int = 0, total: int | None = None) -> Page:
    items = [Resource("BookDTO", {"id": index}, []) for index in range(count)]
    info = page_info(number, 12, count if total is None else total)
    return Page("books", items, page_links(BASE, info, "asc"), info)


def test_json_page_is_hal() -> None:
    body = json.loads(render(MediaType.JSON, make_page(2, total=30)))
    assert list(body) == ["_embedded", "_links", "page"]
    assert [item["id"] for item in body["_embedded"]["books"]] == [0, 1]
    assert body["page"] == {"number": 0, "size": 12, "totalElements": 30, "totalPages": 3}


def test_json_empty_page_has_no_embedded() -> None:
    body = json.loads(render(MediaType.JSON, make_page(0)))
    assert "_embedded" not in body
    assert list(body["_links"]) == ["self"]
    assert body["page"]["totalPages"] == 0


def test_xml_page_nests_content_twice() -> None:
    raw = render(MediaType.XML, make_page(2, total=30)).decode()
    assert raw.startswith("<PagedModel><content><content><id>0</id></content><content><id>1</id>")
    assert raw.endswith(
        "<page><number>0</number><size>12</size><totalElements>30</totalElements><totalPages>3</totalPages></page></PagedModel>"
    )


def test_xml_and_yaml_empty_page() -> None:
    assert render(MediaType.XML, make_page(0)).decode().startswith("<PagedModel><content /><links>")
    assert render(MediaType.YAML, make_page(0)).decode().startswith("---\ncontent: []\nlinks:\n")


def test_resource_list_is_plain_array_root_list_and_item() -> None:
    items = ResourceList([Resource("PersonDTO", {"id": 7}, [Link("self", "http://h/7", "GET")])])
    assert json.loads(render(MediaType.JSON, items)) == [
        {"id": 7, "links": [{"rel": "self", "href": "http://h/7", "type": "GET"}]}
    ]
    assert render(MediaType.XML, items).decode().startswith("<List><item><id>7</id><links>")


def test_plain_keeps_declared_order() -> None:
    error = Plain("ExceptionResponse", {"timestamp": "t", "message": "m", "details": "d"})
    assert list(json.loads(render(MediaType.JSON, error))) == ["timestamp", "message", "details"]
    assert render(MediaType.XML, error).decode() == (
        "<ExceptionResponse><timestamp>t</timestamp><message>m</message><details>d</details></ExceptionResponse>"
    )


@pytest.mark.parametrize(
    ("number", "total", "rels"),
    [
        (0, 0, ["self"]),
        (0, 30, ["first", "self", "next", "last"]),
        (1, 30, ["first", "prev", "self", "next", "last"]),
        (2, 30, ["first", "prev", "self", "last"]),
        (99999, 30, ["first", "prev", "self", "last"]),
    ],
)
def test_page_links(number: int, total: int, rels: list[str]) -> None:
    links = page_links(BASE, PageInfo(number, 12, total, -(-total // 12)), "desc")
    assert [link.rel for link in links] == rels
    assert (
        links[rels.index("self")].href
        == f"http://h/api/book/v1?page={number}&size=12&direction=desc"
    )


def test_parse_xml_reads_nested_lists_and_nil() -> None:
    raw = (
        b'<PersonDTO xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><id>1</id>'
        b'<photoUrl xsi:nil="true"/><links><rel>a</rel></links>'
        b"<links><rel>b</rel></links></PersonDTO>"
    )
    assert parse_xml(raw) == {"id": "1", "photoUrl": None, "links": [{"rel": "a"}, {"rel": "b"}]}


@pytest.mark.parametrize(
    "raw",
    [
        b"not xml",
        b"<a><b></a>",
        b'<!DOCTYPE a [<!ENTITY x "boom">]><a><b>&x;</b></a>',
        b"<a>text only</a>",
    ],
)
def test_parse_xml_rejects_malformed_and_dangerous_documents(raw: bytes) -> None:
    with pytest.raises(MalformedBodyError):
        parse_xml(raw)


def test_parse_yaml() -> None:
    assert parse_yaml(b"firstName: Linus\nage: 3\n") == {"firstName": "Linus", "age": 3}
    for raw in (b"- a\n- b\n", b"just text", b"a: [unclosed"):
        with pytest.raises(MalformedBodyError):
            parse_yaml(raw)


def test_yaml_does_not_construct_arbitrary_objects() -> None:
    with pytest.raises(MalformedBodyError):
        parse_yaml(b"a: !!python/object/apply:os.system ['echo boom']")


def test_to_json_body_converts_and_keeps_empty() -> None:
    assert json.loads(to_json_body(MediaType.YAML, b"launchDate: 2024-01-01\n")) == {
        "launchDate": "2024-01-01"
    }
    assert to_json_body(MediaType.XML, b"  ") == b"  "

import pytest

from erudio.core.negotiation.media import MediaType, request_media_type, select_media_type

JSON, XML, YAML = MediaType.JSON, MediaType.XML, MediaType.YAML


@pytest.mark.parametrize(
    ("accept", "expected"),
    [
        (None, JSON),
        ("", JSON),
        ("*/*", JSON),
        ("application/*", JSON),
        ("application/json", JSON),
        ("application/xml", XML),
        ("application/yaml", YAML),
        ("application/xml, application/json", XML),
        ("application/json;q=0.5, application/xml", XML),
        ("application/json;q=0.5, application/xml;q=0.9, application/yaml", YAML),
        ("text/html, application/xml;q=0.8", XML),
        ("text/html, */*;q=0.1", JSON),
        ("application/xml;q=0, */*", JSON),
        ("text/html", None),
        ("application/pdf", None),
        ("garbage", None),
    ],
)
def test_select_media_type(accept: str | None, expected: MediaType | None) -> None:
    assert select_media_type(accept) is expected


@pytest.mark.parametrize(
    ("content_type", "expected"),
    [
        ("application/json", JSON),
        ("application/json; charset=utf-8", JSON),
        ("application/vnd.api+json", JSON),
        ("application/xml", XML),
        ("application/yaml", YAML),
        ("application/x-yaml", YAML),
        ("text/plain", None),
        ("multipart/form-data; boundary=x", None),
        (None, None),
    ],
)
def test_request_media_type(content_type: str | None, expected: MediaType | None) -> None:
    assert request_media_type(content_type) is expected

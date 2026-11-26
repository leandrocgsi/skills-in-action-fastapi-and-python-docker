import re
from typing import Any

import yaml
from httpx import AsyncClient, Response

from erudio.core.negotiation.formats import parse_xml
from erudio.core.negotiation.media import MediaType

TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")


def parse(response: Response) -> Any:
    kind = response.headers["content-type"].split(";")[0]
    if kind == MediaType.JSON.value:
        return response.json()
    if kind == MediaType.XML.value:
        return parse_xml(response.content)
    return yaml.safe_load(response.content)


async def assert_problem(
    response: Response, status: int, detail: str | None = None
) -> dict[str, Any]:
    assert response.status_code == status
    assert response.headers["content-type"] == "application/problem+json"
    body: dict[str, Any] = response.json()
    assert body["type"] == "about:blank"
    assert body["status"] == status
    assert body["instance"] == response.request.url.path
    if detail is not None:
        assert body["detail"] == detail
    return body


async def all_pages(client: AsyncClient, url: str, embedded: str, **params: Any) -> list[Any]:
    """Follows a HAL collection page by page (the page size is capped) and joins the items."""
    items: list[Any] = []
    page = 0
    while True:
        body = (await client.get(url, params={**params, "page": page})).json()
        items.extend(body.get("_embedded", {}).get(embedded, []))
        page += 1
        if page >= body["page"]["totalPages"]:
            return items

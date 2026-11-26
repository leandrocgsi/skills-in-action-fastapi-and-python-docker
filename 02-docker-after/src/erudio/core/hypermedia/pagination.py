import math
from typing import Annotated

from fastapi import Query
from starlette.datastructures import URL

from erudio.core.hypermedia.models import Link, PageInfo

# `page` is bounded like Java's Integer (it also keeps `page * size` inside what MySQL accepts
# for OFFSET); `size` is capped at the default page size, so a client cannot ask for the table.
INT_MAX = 2_147_483_647
MAX_PAGE_SIZE = 12
PageParam = Annotated[int, Query(ge=0, le=INT_MAX)]
SizeParam = Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)]


def page_info(number: int, size: int, total_elements: int) -> PageInfo:
    return PageInfo(number, size, total_elements, math.ceil(total_elements / size))


def page_links(base: URL, info: PageInfo, direction: str) -> list[Link]:
    def link(rel: str, number: int) -> Link:
        return Link(
            rel, str(base.include_query_params(page=number, size=info.size, direction=direction))
        )

    links: list[Link] = []
    has_pages = info.total_pages > 0
    if has_pages:
        links.append(link("first", 0))
        if info.number > 0:
            links.append(link("prev", info.number - 1))
    links.append(link("self", info.number))
    if has_pages:
        if info.number + 1 < info.total_pages:
            links.append(link("next", info.number + 1))
        links.append(link("last", info.total_pages - 1))
    return links

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Link:
    rel: str
    href: str
    type: str | None = None
    title: str | None = None


@dataclass(frozen=True, slots=True)
class Resource:
    root: str
    data: Mapping[str, Any]
    links: Sequence[Link] = ()


@dataclass(frozen=True, slots=True)
class PageInfo:
    number: int
    size: int
    total_elements: int
    total_pages: int


@dataclass(frozen=True, slots=True)
class Page:
    embedded: str
    items: Sequence[Resource]
    links: Sequence[Link]
    info: PageInfo


@dataclass(frozen=True, slots=True)
class ResourceList:
    items: Sequence[Resource]


@dataclass(frozen=True, slots=True)
class Plain:
    root: str
    data: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class PlainList:
    items: Sequence[Mapping[str, Any]]


type Renderable = Resource | Page | ResourceList | Plain | PlainList

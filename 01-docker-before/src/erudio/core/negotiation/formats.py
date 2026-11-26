import json
from collections.abc import Mapping
from typing import Any
from xml.etree import ElementTree as ET

import yaml
from defusedxml import ElementTree as SafeET

from erudio.core.errors import MalformedBodyError
from erudio.core.hypermedia.models import (
    Link,
    Page,
    Plain,
    PlainList,
    Renderable,
    Resource,
    ResourceList,
)
from erudio.core.negotiation.media import MediaType

XSI = "http://www.w3.org/2001/XMLSchema-instance"
ET.register_namespace("xsi", XSI)


def _link(link: Link, *, with_rel: bool) -> dict[str, str]:
    body: dict[str, str] = {}
    if with_rel:
        body["rel"] = link.rel
    body["href"] = link.href
    if link.title is not None:
        body["title"] = link.title
    if link.type is not None:
        body["type"] = link.type
    return body


def _plain_fields(resource: Resource) -> dict[str, Any]:
    fields: dict[str, Any] = dict(resource.data)
    if resource.links:
        fields["links"] = [_link(link, with_rel=True) for link in resource.links]
    return dict(sorted(fields.items()))


def _hal_fields(resource: Resource) -> dict[str, Any]:
    body: dict[str, Any] = {}
    if resource.links:
        body["_links"] = {link.rel: _link(link, with_rel=False) for link in resource.links}
    body.update(sorted(resource.data.items()))
    return body


def _document(value: Renderable, *, hal: bool) -> tuple[str, Any]:
    match value:
        case Resource():
            return value.root, _hal_fields(value) if hal else _plain_fields(value)
        case Page():
            info = {
                "number": value.info.number,
                "size": value.info.size,
                "totalElements": value.info.total_elements,
                "totalPages": value.info.total_pages,
            }
            if hal:
                body: dict[str, Any] = {}
                if value.items:
                    body["_embedded"] = {
                        value.embedded: [_hal_fields(item) for item in value.items]
                    }
                body["_links"] = {link.rel: _link(link, with_rel=False) for link in value.links}
                body["page"] = info
                return "PagedModel", body
            return "PagedModel", {
                "content": [_plain_fields(item) for item in value.items],
                "links": [_link(link, with_rel=True) for link in value.links],
                "page": info,
            }
        case ResourceList():
            return "List", [_plain_fields(item) for item in value.items]
        case Plain():
            return value.root, dict(value.data)
        case PlainList():
            return "List", [dict(item) for item in value.items]


def _set(element: ET.Element, value: Any) -> None:
    if value is None:
        element.set(f"{{{XSI}}}nil", "true")
    elif isinstance(value, Mapping):
        for key, child in value.items():
            _fill(element, key, child)
    elif isinstance(value, bool):
        element.text = "true" if value else "false"
    else:
        element.text = str(value)


def _fill(parent: ET.Element, key: str, value: Any) -> None:
    if isinstance(value, list):
        for item in value:
            _fill(parent, key, item)
    else:
        _set(ET.SubElement(parent, key), value)


def _xml(value: Renderable, root: str, structure: Any) -> bytes:
    element = ET.Element(root)
    if isinstance(value, ResourceList | PlainList):
        for item in structure:
            _set(ET.SubElement(element, "item"), item)
    elif isinstance(value, Page):
        content = ET.SubElement(element, "content")
        for item in structure["content"]:
            _set(ET.SubElement(content, "content"), item)
        _fill(element, "links", structure["links"])
        _fill(element, "page", structure["page"])
    else:
        _set(element, structure)
    return ET.tostring(element, encoding="unicode").encode()


class _Quoted(str):
    __slots__ = ()


class _Dumper(yaml.SafeDumper):
    def ignore_aliases(self, data: Any) -> bool:
        return True


def _represent_quoted(dumper: yaml.SafeDumper, data: _Quoted) -> yaml.ScalarNode:
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data), style='"')


_Dumper.add_representer(_Quoted, _represent_quoted)


def _quote_values(node: Any) -> Any:
    if isinstance(node, str):
        return _Quoted(node)
    if isinstance(node, Mapping):
        return {key: _quote_values(value) for key, value in node.items()}
    if isinstance(node, list):
        return [_quote_values(item) for item in node]
    return node


def render(media: MediaType, value: Renderable) -> bytes:
    root, structure = _document(value, hal=media is MediaType.JSON)
    match media:
        case MediaType.JSON:
            return json.dumps(structure, ensure_ascii=False, separators=(",", ":")).encode()
        case MediaType.XML:
            return _xml(value, root, structure)
        case MediaType.YAML:
            return yaml.dump(
                _quote_values(structure),
                Dumper=_Dumper,
                sort_keys=False,
                allow_unicode=True,
                explicit_start=True,
                default_flow_style=False,
                width=2**31 - 1,
            ).encode()


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _element_value(element: ET.Element) -> Any:
    if element.get(f"{{{XSI}}}nil") == "true":
        return None
    children = list(element)
    if not children:
        return element.text or ""
    buckets: dict[str, list[Any]] = {}
    for child in children:
        buckets.setdefault(_local_name(child.tag), []).append(_element_value(child))
    return {name: values[0] if len(values) == 1 else values for name, values in buckets.items()}


def parse_xml(raw: bytes) -> dict[str, Any]:
    try:
        root = SafeET.fromstring(raw)
    except Exception as error:
        raise MalformedBodyError from error
    value = _element_value(root)
    if isinstance(value, dict):
        return value
    if value == "":
        return {}
    raise MalformedBodyError


def parse_yaml(raw: bytes) -> dict[str, Any]:
    try:
        value = yaml.safe_load(raw)
    except yaml.YAMLError as error:
        raise MalformedBodyError from error
    if isinstance(value, dict):
        return value
    raise MalformedBodyError


def to_json_body(media: MediaType, raw: bytes) -> bytes:
    if not raw.strip():
        return raw
    data = parse_xml(raw) if media is MediaType.XML else parse_yaml(raw)
    return json.dumps(data, default=str).encode()

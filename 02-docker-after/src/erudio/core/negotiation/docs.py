from typing import Any

from pydantic import BaseModel

from erudio.core.negotiation.media import MediaType

type Responses = dict[int | str, dict[str, Any]]

_LINK: dict[str, Any] = {
    "type": "object",
    "properties": {
        "href": {"type": "string"},
        "type": {"type": "string"},
        "title": {"type": "string"},
    },
}
_PAGE: dict[str, Any] = {
    "type": "object",
    "properties": {
        "number": {"type": "integer"},
        "size": {"type": "integer"},
        "totalElements": {"type": "integer"},
        "totalPages": {"type": "integer"},
    },
}


def _ref(model: type[BaseModel]) -> dict[str, str]:
    return {"$ref": f"#/components/schemas/{model.__name__}"}


def item_responses(model: type[BaseModel], description: str = "Successful Response") -> Responses:
    schema = {"schema": _ref(model)}
    return {
        200: {
            "description": description,
            "model": model,
            "content": {MediaType.XML.value: schema, MediaType.YAML.value: schema},
        }
    }


def list_responses(model: type[BaseModel], description: str = "Successful Response") -> Responses:
    schema = {"schema": {"type": "array", "items": _ref(model)}}
    return {
        200: {
            "description": description,
            "model": list[model],  # type: ignore[valid-type]
            "content": {MediaType.XML.value: schema, MediaType.YAML.value: schema},
        }
    }


def page_responses(
    model: type[BaseModel], embedded: str, description: str = "Successful Response"
) -> Responses:
    hal = {
        "type": "object",
        "properties": {
            "_embedded": {
                "type": "object",
                "properties": {embedded: {"type": "array", "items": _ref(model)}},
            },
            "_links": {"type": "object", "additionalProperties": _LINK},
            "page": _PAGE,
        },
    }
    plain = {
        "type": "object",
        "properties": {
            "content": {"type": "array", "items": _ref(model)},
            "links": {
                "type": "array",
                "items": {
                    **_LINK,
                    "properties": {"rel": {"type": "string"}, **_LINK["properties"]},
                },
            },
            "page": _PAGE,
        },
    }
    return {
        200: {
            "description": description,
            "content": {
                MediaType.JSON.value: {"schema": hal},
                MediaType.XML.value: {"schema": plain},
                MediaType.YAML.value: {"schema": plain},
            },
        }
    }


def body_docs(model: type[BaseModel]) -> dict[str, Any]:
    schema = {"schema": _ref(model)}
    return {"requestBody": {"content": {MediaType.XML.value: schema, MediaType.YAML.value: schema}}}

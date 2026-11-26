from typing import Any

from fastapi import FastAPI

PROBLEM_DETAIL: dict[str, Any] = {
    "type": "object",
    "properties": {
        "type": {"type": "string", "example": "about:blank"},
        "title": {"type": "string"},
        "status": {"type": "integer"},
        "detail": {"type": "string"},
        "instance": {"type": "string"},
        "errors": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "in": {"type": "string"},
                    "field": {"type": "string"},
                    "message": {"type": "string"},
                },
            },
        },
    },
}

EXCEPTION_RESPONSE: dict[str, Any] = {
    "type": "object",
    "properties": {
        "timestamp": {"type": "string", "format": "date-time"},
        "message": {"type": "string"},
        "details": {"type": "string", "example": "uri=/api/book/v1/999"},
    },
}


HTTP_METHODS = {"get", "put", "post", "delete", "patch"}


def problem_docs(description: str) -> dict[str, Any]:
    return {
        "description": description,
        "content": {
            "application/problem+json": {"schema": {"$ref": "#/components/schemas/ProblemDetail"}}
        },
    }


def exception_docs(description: str, *, or_problem: bool = False) -> dict[str, Any]:
    media = {"schema": {"$ref": "#/components/schemas/ExceptionResponse"}}
    content = {"application/json": media, "application/xml": media, "application/yaml": media}
    if or_problem:
        content["application/problem+json"] = problem_docs("")["content"][
            "application/problem+json"
        ]
    return {"description": description, "content": content}


def _document_errors(path: str, method: str, operation: dict[str, Any]) -> None:
    responses = operation.setdefault("responses", {})
    responses.pop("422", None)
    has_body = "requestBody" in operation
    if has_body or operation.get("parameters"):
        responses.setdefault("400", problem_docs("Bad Request"))
    if operation.get("security"):
        responses.setdefault("401", problem_docs("Unauthorized"))
    if path.startswith("/api/") and ("{" in path or method == "put"):
        responses.setdefault("404", exception_docs("Not Found"))
    responses.setdefault("406", problem_docs("Not Acceptable"))
    if has_body:
        responses.setdefault("415", problem_docs("Unsupported Media Type"))
        if "multipart/form-data" in operation["requestBody"].get("content", {}):
            responses.setdefault("413", problem_docs("Payload Too Large"))
    responses.setdefault("500", exception_docs("Internal Server Error"))


def _customize(schema: dict[str, Any]) -> None:
    for path, operations in schema.get("paths", {}).items():
        for method, operation in operations.items():
            if method in HTTP_METHODS:
                _document_errors(path, method, operation)
    components = schema.setdefault("components", {}).setdefault("schemas", {})
    components.pop("HTTPValidationError", None)
    components.pop("ValidationError", None)
    components["ProblemDetail"] = PROBLEM_DETAIL
    components["ExceptionResponse"] = EXCEPTION_RESPONSE


def install_error_docs(app: FastAPI) -> None:
    original = app.openapi

    def openapi() -> dict[str, Any]:
        first = app.openapi_schema is None
        schema = original()
        if first:
            _customize(schema)
        return schema

    app.openapi = openapi  # type: ignore[method-assign]

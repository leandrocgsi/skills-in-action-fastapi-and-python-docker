from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Request, Response, params
from fastapi.routing import APIRoute
from starlette.types import Receive, Scope

from erudio.core.auth import authenticate_request, current_user
from erudio.core.errors import UnsupportedMediaTypeError
from erudio.core.negotiation.formats import to_json_body
from erudio.core.negotiation.media import MediaType, request_media_type


class ConvertingRequest(Request):
    def __init__(self, scope: Scope, receive: Receive, media: MediaType) -> None:
        super().__init__(scope, receive)
        self._media = media
        self._converted: bytes | None = None

    async def body(self) -> bytes:
        if self._converted is None:
            self._converted = to_json_body(self._media, await super().body())
        return self._converted


def _has_body(request: Request) -> bool:
    length = request.headers.get("content-length", "0")
    return (length.isdigit() and int(length) > 0) or "transfer-encoding" in request.headers


def negotiate_request(request: Request) -> Request:
    content_type = request.headers.get("content-type")
    media = request_media_type(content_type)
    if media is None:
        if content_type is None and not _has_body(request):
            return request
        raise UnsupportedMediaTypeError(content_type)
    if media is MediaType.JSON:
        return request
    scope = dict(request.scope)
    scope["headers"] = [
        (name, b"application/json" if name == b"content-type" else value)
        for name, value in request.scope["headers"]
    ]
    return ConvertingRequest(scope, request.receive, media)


def require_multipart(request: Request) -> None:
    content_type = request.headers.get("content-type")
    if content_type is None or not content_type.lower().startswith("multipart/form-data"):
        raise UnsupportedMediaTypeError(content_type)


class NegotiatingRoute(APIRoute):
    """Route that reads JSON, XML and YAML bodies and enforces multipart on upload routes."""

    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        original = super().get_route_handler()
        is_form = self.body_field is not None and isinstance(
            self.body_field.field_info, params.Form
        )
        is_protected = any(item.call is current_user for item in self.dependant.dependencies)

        async def handler(request: Request) -> Response:
            if not is_form:
                return await original(
                    negotiate_request(request) if self.body_field is not None else request
                )
            # FastAPI parses (and spools to disk) a multipart body before it resolves
            # dependencies, so a bad token is rejected here, before any upload is read.
            if is_protected:
                authenticate_request(request, request.app.state.settings)
            require_multipart(request)
            return await original(request)

        return handler

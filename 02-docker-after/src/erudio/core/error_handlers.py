import logging
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.routing import Match

from erudio.core.errors import (
    ApiError,
    AuthenticationRequiredError,
    MalformedBodyError,
    NotAcceptableError,
    PayloadTooLargeError,
    UnsupportedMediaTypeError,
)
from erudio.core.hypermedia.models import Plain
from erudio.core.negotiation.media import MediaType, select_media_type
from erudio.core.negotiation.responder import render_response
from erudio.core.timeutil import format_timestamp, utc_now

logger = logging.getLogger(__name__)

FAILED_TO_READ = "Failed to read request"
FASTAPI_BODY_ERROR = "There was an error parsing the body"
BODY_LEVEL_ERRORS = {"json_invalid", "model_attributes_type", "model_type"}


def problem(
    request: Request,
    status: int,
    detail: str,
    errors: list[dict[str, str]] | None = None,
    headers: dict[str, str] | None = None,
) -> Response:
    body: dict[str, Any] = {
        "detail": detail,
        "instance": request.url.path,
        "status": status,
        "title": HTTPStatus(status).phrase,
        "type": "about:blank",
    }
    if errors:
        body["errors"] = errors
    return JSONResponse(
        dict(sorted(body.items())),
        status_code=status,
        media_type="application/problem+json",
        headers=headers,
    )


def exception_response(request: Request, status: int, message: str) -> Response:
    media = select_media_type(request.headers.get("accept")) or MediaType.JSON
    body = Plain(
        "ExceptionResponse",
        {
            "timestamp": format_timestamp(utc_now()),
            "message": message,
            "details": f"uri={request.url.path}",
        },
    )
    return render_response(media, body, status)


def _is_body_level(error: Any) -> bool:
    return error["type"] in BODY_LEVEL_ERRORS or (
        error["type"] == "missing" and tuple(error["loc"]) == ("body",)
    )


def _allowed_methods(request: Request) -> str:
    allowed = []
    for method in ("GET", "POST", "PUT", "PATCH", "DELETE"):
        scope = {**request.scope, "method": method}
        if any(route.matches(scope)[0] is Match.FULL for route in request.app.router.routes):
            allowed.append(method)
    return ", ".join(sorted(allowed))


def _field_errors(exc: RequestValidationError) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    for error in exc.errors():
        location = [str(part) for part in error["loc"]]
        source = location[0] if location else "body"
        errors.append({"in": source, "field": ".".join(location[1:]), "message": str(error["msg"])})
    return errors


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def api_error(request: Request, exc: ApiError) -> Response:
        return exception_response(request, exc.status, exc.message)

    @app.exception_handler(AuthenticationRequiredError)
    async def authentication_required(
        request: Request, exc: AuthenticationRequiredError
    ) -> Response:
        return problem(
            request,
            401,
            "Full authentication is required to access this resource",
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(NotAcceptableError)
    async def not_acceptable(request: Request, exc: NotAcceptableError) -> Response:
        return problem(request, 406, str(exc))

    @app.exception_handler(UnsupportedMediaTypeError)
    async def unsupported_media_type(request: Request, exc: UnsupportedMediaTypeError) -> Response:
        return problem(request, 415, str(exc))

    @app.exception_handler(PayloadTooLargeError)
    async def payload_too_large(request: Request, exc: PayloadTooLargeError) -> Response:
        return problem(request, 413, str(exc))

    @app.exception_handler(MalformedBodyError)
    async def malformed_body(request: Request, exc: MalformedBodyError) -> Response:
        return problem(request, 400, FAILED_TO_READ)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> Response:
        body_level = any(_is_body_level(error) for error in exc.errors())
        detail = FAILED_TO_READ if body_level else "Validation failed for the request"
        return problem(request, 400, detail, None if body_level else _field_errors(exc))

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> Response:
        detail = str(exc.detail)
        if exc.status_code == 404:
            detail = f"No static resource {request.url.path.lstrip('/')}."
        elif exc.status_code == 405:
            detail = f"Method '{request.method}' is not supported."
        elif exc.status_code == 400 and detail == FASTAPI_BODY_ERROR:
            detail = FAILED_TO_READ
        headers = dict(exc.headers) if exc.headers else None
        if exc.status_code == 405:
            headers = {**(headers or {}), "Allow": _allowed_methods(request)}
        return problem(request, exc.status_code, detail, headers=headers)

    @app.exception_handler(Exception)
    async def unexpected(request: Request, exc: Exception) -> Response:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path, exc_info=exc)
        return exception_response(request, 500, "An unexpected error occurred.")

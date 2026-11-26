from collections.abc import Mapping
from typing import Annotated

from fastapi import Depends, Request, Response

from erudio.core.errors import NotAcceptableError
from erudio.core.hypermedia.models import Renderable
from erudio.core.negotiation.formats import render
from erudio.core.negotiation.media import OFFERED, MediaType, select_media_type


def render_response(
    media: MediaType,
    value: Renderable,
    status_code: int = 200,
    headers: Mapping[str, str] | None = None,
) -> Response:
    return Response(
        content=render(media, value),
        status_code=status_code,
        media_type=media.value,
        headers=dict(headers) if headers else None,
    )


class Responder:
    def __init__(self, request: Request) -> None:
        self._request = request

    def __call__(self, value: Renderable, status_code: int = 200) -> Response:
        media = select_media_type(self._request.headers.get("accept"))
        if media is None:
            raise NotAcceptableError([offered.value for offered in OFFERED])
        return render_response(media, value, status_code)


def get_responder(request: Request) -> Responder:
    return Responder(request)


RespondDep = Annotated[Responder, Depends(get_responder)]

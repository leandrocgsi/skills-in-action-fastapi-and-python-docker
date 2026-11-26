from starlette.datastructures import Headers
from starlette.exceptions import HTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from erudio.core.errors import MAX_UPLOAD_EXCEEDED


class RequestSizeLimitMiddleware:
    """Rejects a request whose body is larger than the limit, declared or streamed."""

    def __init__(self, app: ASGIApp, *, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        declared = Headers(scope=scope).get("content-length", "")
        received = 0

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes or (
                    declared.isdigit() and int(declared) > self.max_bytes
                ):
                    raise HTTPException(413, MAX_UPLOAD_EXCEEDED)
            return message

        await self.app(scope, limited_receive, send)

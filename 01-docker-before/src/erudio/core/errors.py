class ApiError(Exception):
    status = 500
    default_message = "Internal Server Error"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class ResourceNotFoundError(ApiError):
    status = 404
    default_message = "No records found for this ID!"


class StoredFileNotFoundError(ApiError):
    status = 404
    default_message = "File not found"


class BadRequestError(ApiError):
    status = 400
    default_message = "Bad Request"


class InvalidCredentialsError(ApiError):
    status = 401
    default_message = "Bad credentials"


class InvalidJwtError(ApiError):
    status = 401
    default_message = "Expired or Invalid JWT Token!"


class ForbiddenError(ApiError):
    status = 403
    default_message = "Forbidden"


class ConflictError(ApiError):
    status = 409
    default_message = "Conflict"


class BadGatewayError(ApiError):
    status = 502
    default_message = "Bad Gateway"


MAX_UPLOAD_EXCEEDED = "Maximum upload size exceeded"


class PayloadTooLargeError(Exception):
    def __init__(self) -> None:
        super().__init__(MAX_UPLOAD_EXCEEDED)


class AuthenticationRequiredError(Exception):
    pass


class NotAcceptableError(Exception):
    def __init__(self, offered: list[str]) -> None:
        self.offered = offered
        super().__init__(f"Acceptable representations: [{', '.join(offered)}].")


class UnsupportedMediaTypeError(Exception):
    def __init__(self, content_type: str | None) -> None:
        self.content_type = content_type
        super().__init__(f"Content-Type '{content_type}' is not supported.")


class MalformedBodyError(Exception):
    pass

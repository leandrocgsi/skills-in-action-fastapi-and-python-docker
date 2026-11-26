from pydantic import ValidationError

from erudio.core.config import Settings
from erudio.core.errors import BadRequestError
from erudio.mail import smtp
from erudio.schemas.email import EmailRequest, StrictEmailRequest


def _text_or(value: str | None, default: str) -> str:
    return value if value and value.strip() else default


async def _deliver(
    settings: Settings, request: EmailRequest, attachment: smtp.Attachment | None = None
) -> None:
    recipients = smtp.parse_recipients(request.to)
    if not settings.email_username:
        msg = "EMAIL_USERNAME is not configured"
        raise RuntimeError(msg)
    message = smtp.build_message(
        settings.email_username,
        recipients,
        _text_or(request.subject, settings.email_default_subject),
        _text_or(request.body, settings.email_default_message),
        attachment,
    )
    await smtp.send(settings, message)


async def send_simple(settings: Settings, request: EmailRequest) -> None:
    await _deliver(settings, request)


async def send_with_attachment(
    settings: Settings, request_json: str, filename: str, content: bytes
) -> None:
    try:
        request = StrictEmailRequest.model_validate_json(request_json)
    except ValidationError as error:
        raise BadRequestError("Error parsing email request JSON!") from error
    await _deliver(settings, request, smtp.Attachment(filename, content))

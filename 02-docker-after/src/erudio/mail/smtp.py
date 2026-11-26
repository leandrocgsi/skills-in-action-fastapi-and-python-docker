import logging
import mimetypes
from dataclasses import dataclass
from email.message import EmailMessage

import aiosmtplib
from email_validator import EmailNotValidError, validate_email

from erudio.core.config import Settings
from erudio.core.errors import BadGatewayError, BadRequestError

logger = logging.getLogger(__name__)

SMTP_TIMEOUT_SECONDS = 15
MIME_TYPES = mimetypes.MimeTypes()


@dataclass(frozen=True, slots=True)
class Attachment:
    filename: str
    content: bytes


def parse_recipients(to: str) -> list[str]:
    """Splits `a@x.com; b@y.com` (whitespace ignored) and validates every address."""
    addresses = [part for part in "".join(to.split()).split(";") if part]
    if not addresses:
        raise BadRequestError("At least one recipient is required")
    for address in addresses:
        try:
            validate_email(address, check_deliverability=False)
        except EmailNotValidError as error:
            raise BadRequestError(f"Invalid e-mail address: {address}") from error
    return addresses


def build_message(
    sender: str,
    recipients: list[str],
    subject: str,
    body: str,
    attachment: Attachment | None = None,
) -> EmailMessage:
    message = EmailMessage()
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message.set_content(body, subtype="html")
    if attachment is not None:
        media_type = MIME_TYPES.guess_type(attachment.filename)[0] or "application/octet-stream"
        maintype, _, subtype = media_type.partition("/")
        message.add_attachment(
            attachment.content, maintype=maintype, subtype=subtype, filename=attachment.filename
        )
    return message


async def send(settings: Settings, message: EmailMessage) -> None:
    logs_in = bool(settings.email_username and settings.email_password)
    try:
        await aiosmtplib.send(
            message,
            hostname=settings.mail_host,
            port=settings.mail_port,
            username=settings.email_username if logs_in else None,
            password=settings.email_password if logs_in else None,
            start_tls=settings.mail_starttls,
            timeout=SMTP_TIMEOUT_SECONDS,
        )
    except (aiosmtplib.SMTPException, OSError) as error:
        logger.error("Error sending the email: %s", error)
        raise BadGatewayError("Error sending the email") from error
    logger.info("Email sent to %s with the subject '%s'", message["To"], message["Subject"])

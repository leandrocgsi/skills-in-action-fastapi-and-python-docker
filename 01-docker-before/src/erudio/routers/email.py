from typing import Annotated

from fastapi import APIRouter, Depends, Form, Response, UploadFile
from fastapi.responses import PlainTextResponse

from erudio.core.auth import current_user
from erudio.core.dependencies import SettingsDep
from erudio.core.negotiation.docs import Responses
from erudio.core.negotiation.route import NegotiatingRoute
from erudio.core.openapi import exception_docs
from erudio.schemas.email import EmailRequest
from erudio.services import email as email_service

router = APIRouter(
    prefix="/api/email/v1",
    tags=["Email Endpoint"],
    route_class=NegotiatingRoute,
    dependencies=[Depends(current_user)],
)

PLAIN_TEXT: Responses = {
    200: {"description": "Success", "content": {"text/plain": {}}},
    400: exception_docs("Invalid recipient or e-mail request", or_problem=True),
    502: exception_docs("The SMTP server refused or could not be reached"),
}


@router.post(
    "",
    name="email_send",
    summary="Send an e-Mail",
    description="Sends an e-mail by providing details, subject and body!",
    response_class=PlainTextResponse,
    responses=PLAIN_TEXT,
)
async def send_email(settings: SettingsDep, email_request: EmailRequest) -> Response:
    await email_service.send_simple(settings, email_request)
    return PlainTextResponse("e-Mail sent with success!")


@router.post(
    "/withAttachment",
    name="email_send_with_attachment",
    summary="Send an e-Mail with Attachment",
    description="Sends an e-mail with Attachment by providing details, subject and body!",
    response_class=PlainTextResponse,
    responses=PLAIN_TEXT,
)
async def send_email_with_attachment(
    settings: SettingsDep,
    email_request: Annotated[str, Form(alias="emailRequest")],
    attachment: UploadFile,
) -> Response:
    await email_service.send_with_attachment(
        settings, email_request, attachment.filename or "attachment", await attachment.read()
    )
    return PlainTextResponse("e-Mail with attachment sent successfully!")

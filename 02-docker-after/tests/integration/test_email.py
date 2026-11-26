import json
from email.message import EmailMessage

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, Response

from erudio.core.negotiation.media import MediaType
from tests.conftest import SmtpInbox, free_port
from tests.helpers import TIMESTAMP, assert_problem

pytestmark = pytest.mark.integration

BASE = "/api/email/v1"
JSON, XML, YAML = MediaType.JSON.value, MediaType.XML.value, MediaType.YAML.value
REQUEST = {"to": "mary@erudio.com.br", "subject": "Hello", "body": "<b>Hi</b>"}


def body_of(message: EmailMessage) -> str:
    part = message.get_body(preferencelist=("html", "plain"))
    assert part is not None
    return str(part.get_content()).strip()


async def with_attachment(
    client: AsyncClient,
    request: object,
    name: str = "notes.txt",
    content: bytes = b"attached text",
    kind: str = "text/plain",
) -> Response:
    text = request if isinstance(request, str) else json.dumps(request)
    return await client.post(
        f"{BASE}/withAttachment",
        data={"emailRequest": text},
        files={"attachment": (name, content, kind)},
    )


async def test_sends_an_html_message(client: AsyncClient, inbox: SmtpInbox) -> None:
    response = await client.post(BASE, json=REQUEST)

    assert response.status_code == 200
    assert response.headers["content-type"].split(";")[0] == "text/plain"
    assert response.text == "e-Mail sent with success!"
    (message,) = inbox.messages
    assert message["From"] == "sender@erudio.test"
    assert message["To"] == "mary@erudio.com.br"
    assert message["Subject"] == "Hello"
    assert message.get_content_type() == "text/html"
    assert body_of(message) == "<b>Hi</b>"


@pytest.mark.parametrize(
    ("content_type", "body"),
    [
        (
            XML,
            b"<EmailRequestDTO><to>mary@erudio.com.br</to><subject>Hi</subject></EmailRequestDTO>",
        ),
        (YAML, b"to: mary@erudio.com.br\nsubject: Hi\n"),
    ],
)
async def test_reads_xml_and_yaml_requests(
    client: AsyncClient, inbox: SmtpInbox, content_type: str, body: bytes
) -> None:
    response = await client.post(BASE, content=body, headers={"Content-Type": content_type})

    assert response.status_code == 200
    assert inbox.messages[0]["Subject"] == "Hi"


@pytest.mark.parametrize(
    "request_body",
    [{"to": "mary@erudio.com.br"}, {"to": "mary@erudio.com.br", "subject": " ", "body": ""}],
)
async def test_empty_subject_and_body_use_the_configured_defaults(
    client: AsyncClient, inbox: SmtpInbox, request_body: dict[str, str]
) -> None:
    await client.post(BASE, json=request_body)

    (message,) = inbox.messages
    assert message["Subject"] == "Default Subject"
    assert body_of(message) == "Default Message"


async def test_recipients_are_separated_by_semicolons(
    client: AsyncClient, inbox: SmtpInbox
) -> None:
    to = "a@erudio.com.br ; b@erudio.com.br;\n c@erudio.com.br;"

    response = await client.post(BASE, json={**REQUEST, "to": to})

    assert response.status_code == 200
    assert inbox.messages[0]["To"] == "a@erudio.com.br, b@erudio.com.br, c@erudio.com.br"


@pytest.mark.parametrize("to", ["not-an-address@@", "a@erudio.com.br;nope", "plain"])
async def test_an_invalid_recipient_is_a_400(
    client: AsyncClient, inbox: SmtpInbox, to: str
) -> None:
    response = await client.post(BASE, json={**REQUEST, "to": to})

    assert response.status_code == 400
    body = response.json()
    assert list(body) == ["timestamp", "message", "details"]
    assert TIMESTAMP.match(body["timestamp"])
    assert body["message"].startswith("Invalid e-mail address: ")
    assert body["details"] == "uri=/api/email/v1"
    assert inbox.messages == []


async def test_a_blank_recipient_is_a_400(client: AsyncClient) -> None:
    response = await client.post(BASE, json={**REQUEST, "to": " ; "})

    assert response.status_code == 400
    assert response.json()["message"] == "At least one recipient is required"


async def test_a_missing_recipient_is_a_validation_error(client: AsyncClient) -> None:
    body = await assert_problem(await client.post(BASE, json={"subject": "x"}), 400)

    assert {"in": "body", "field": "to", "message": "Field required"} in body["errors"]


@pytest.mark.parametrize("content", [b"{not json", b"null", b""])
async def test_a_malformed_body_is_a_400(client: AsyncClient, content: bytes) -> None:
    response = await client.post(BASE, content=content, headers={"Content-Type": JSON})

    await assert_problem(response, 400)


async def test_a_smtp_failure_is_a_502(client: AsyncClient, app: FastAPI) -> None:
    original = app.state.settings
    app.state.settings = original.model_copy(update={"mail_port": free_port()})
    try:
        response = await client.post(BASE, json=REQUEST)
    finally:
        app.state.settings = original

    assert response.status_code == 502
    assert response.json()["message"] == "Error sending the email"


async def test_it_needs_a_token(anonymous: AsyncClient) -> None:
    response = await anonymous.post(BASE, json=REQUEST)

    assert response.status_code == 401


async def test_sends_an_attachment(client: AsyncClient, inbox: SmtpInbox) -> None:
    response = await with_attachment(client, REQUEST, "notes.txt", b"attached text", "text/plain")

    assert response.status_code == 200
    assert response.text == "e-Mail with attachment sent successfully!"
    (message,) = inbox.messages
    assert message["Subject"] == "Hello"
    assert body_of(message) == "<b>Hi</b>"
    (attachment,) = list(message.iter_attachments())
    assert attachment.get_filename() == "notes.txt"
    assert attachment.get_content_type() == "text/plain"
    assert str(attachment.get_content()) == "attached text"


async def test_a_binary_attachment_keeps_its_bytes(client: AsyncClient, inbox: SmtpInbox) -> None:
    payload = bytes(range(256))

    await with_attachment(client, REQUEST, "data.bin", payload, "application/octet-stream")

    (attachment,) = list(inbox.messages[0].iter_attachments())
    assert attachment.get_content() == payload


@pytest.mark.parametrize(
    "request_json",
    ["{not json", '{"to":"a@erudio.com.br","unknown":1}', '{"subject":"no recipient"}', "[]"],
)
async def test_a_bad_email_request_part_is_a_400(
    client: AsyncClient, inbox: SmtpInbox, request_json: str
) -> None:
    response = await with_attachment(client, request_json)

    assert response.status_code == 400
    assert response.json()["message"] == "Error parsing email request JSON!"
    assert inbox.messages == []


async def test_an_invalid_recipient_with_attachment_is_a_400(client: AsyncClient) -> None:
    response = await with_attachment(client, {"to": "not-an-address@@", "subject": "x"})

    assert response.status_code == 400
    assert response.json()["message"].startswith("Invalid e-mail address")


async def test_a_missing_attachment_is_a_400(client: AsyncClient) -> None:
    response = await client.post(
        f"{BASE}/withAttachment",
        data={"emailRequest": json.dumps(REQUEST)},
        files={"x": ("a", b"")},
    )

    body = await assert_problem(response, 400)
    assert {"in": "body", "field": "attachment", "message": "Field required"} in body["errors"]


async def test_a_missing_email_request_is_a_400(client: AsyncClient) -> None:
    response = await client.post(
        f"{BASE}/withAttachment", files={"attachment": ("a.txt", b"x", "text/plain")}
    )

    body = await assert_problem(response, 400)
    assert {"in": "body", "field": "emailRequest", "message": "Field required"} in body["errors"]


async def test_the_attachment_endpoint_only_takes_multipart(client: AsyncClient) -> None:
    response = await client.post(f"{BASE}/withAttachment", json=REQUEST)

    await assert_problem(response, 415, "Content-Type 'application/json' is not supported.")


async def test_the_attachment_endpoint_needs_a_token(anonymous: AsyncClient) -> None:
    response = await anonymous.post(
        f"{BASE}/withAttachment",
        data={"emailRequest": json.dumps(REQUEST)},
        files={"attachment": ("a.txt", b"x")},
    )

    assert response.status_code == 401

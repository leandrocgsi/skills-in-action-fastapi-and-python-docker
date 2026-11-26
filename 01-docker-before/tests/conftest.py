import os
import socket
import subprocess
import sys
from collections.abc import AsyncIterator, Callable, Iterator
from contextlib import asynccontextmanager
from email import message_from_bytes, policy
from email.message import EmailMessage
from pathlib import Path

import boto3
import pytest
from aiosmtpd.controller import Controller
from aiosmtpd.smtp import SMTP, AuthResult, Envelope, Session
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from testcontainers.community.localstack import LocalStackContainer
from testcontainers.community.mysql import MySqlContainer
from types_boto3_s3 import S3Client

from erudio.core.config import Settings
from erudio.core.database import get_session
from erudio.core.security import issue_tokens
from erudio.main import create_app

ROOT = Path(__file__).resolve().parents[1]
SECRET = "test-secret-key-with-at-least-32-bytes!"
BASE_URL = "http://testserver"


def token_for(
    username: str = "leandro",
    roles: list[str] | None = None,
    *,
    validity_ms: int = 3_600_000,
    secret: str = SECRET,
) -> str:
    roles = ["ADMIN", "MANAGER"] if roles is None else roles
    return issue_tokens(
        username, roles, secret=secret, validity_ms=validity_ms, issuer=BASE_URL
    ).access_token


def migrate(database_url: str) -> None:
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=True,
        cwd=ROOT,
        env={**os.environ, "DATABASE_URL": database_url, "JWT_SECRET_KEY": SECRET},
    )


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    explicit = os.environ.get("TEST_DATABASE_URL")
    if explicit:
        migrate(explicit)
        yield explicit
        return
    with MySqlContainer(
        "mysql:9.7",
        username="erudio",
        password="erudio",
        root_password="erudio",
        dbname="erudio_test",
    ) as mysql:
        host = mysql.get_container_host_ip()
        port = mysql.get_exposed_port(3306)
        url = f"mysql+asyncmy://erudio:erudio@{host}:{port}/erudio_test?charset=utf8mb4"
        migrate(url)
        yield url


TEST_BUCKET = "erudio-files-test"
LOCALSTACK_EDGE_PORT = 4566


@pytest.fixture(scope="session")
def s3_endpoint() -> Iterator[str]:
    with LocalStackContainer(image="localstack/localstack:4.11.1") as localstack:
        host = localstack.get_container_host_ip()
        port = localstack.get_exposed_port(LOCALSTACK_EDGE_PORT)
        yield f"http://{host}:{port}"


@pytest.fixture(scope="session")
def s3_test_client(s3_endpoint: str) -> S3Client:
    return boto3.client(
        "s3",
        region_name="us-east-1",
        endpoint_url=s3_endpoint,
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )


@pytest.fixture(scope="session")
def read_stored_file(s3_test_client: S3Client) -> Callable[[str], bytes]:
    def read(name: str) -> bytes:
        return s3_test_client.get_object(Bucket=TEST_BUCKET, Key=name)["Body"].read()

    return read


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


class SmtpInbox:
    def __init__(self) -> None:
        self.port = free_port()
        self.messages: list[EmailMessage] = []

    async def handle_DATA(self, server: SMTP, session: Session, envelope: Envelope) -> str:
        assert isinstance(envelope.content, bytes)
        self.messages.append(message_from_bytes(envelope.content, policy=policy.default))
        return "250 Message accepted for delivery"


def accept_any_login(*_: object) -> AuthResult:
    return AuthResult(success=True)


@pytest.fixture(scope="session")
def smtp_server() -> Iterator[SmtpInbox]:
    inbox = SmtpInbox()
    controller = Controller(
        inbox,
        hostname="127.0.0.1",
        port=inbox.port,
        authenticator=accept_any_login,
        auth_required=False,
        auth_require_tls=False,
    )
    controller.start()
    yield inbox
    controller.stop()


@pytest.fixture
def inbox(smtp_server: SmtpInbox) -> SmtpInbox:
    smtp_server.messages.clear()
    return smtp_server


@pytest.fixture(scope="session")
def test_settings(database_url: str, s3_endpoint: str, smtp_server: SmtpInbox) -> Settings:
    return Settings(
        database_url=database_url,
        jwt_secret_key=SECRET,
        aws_s3_bucket=TEST_BUCKET,
        aws_s3_endpoint=s3_endpoint,
        mail_host="127.0.0.1",
        mail_port=smtp_server.port,
        mail_starttls=False,
        email_username="sender@erudio.test",
        email_password="secret",
    )


@pytest.fixture(scope="session")
async def app(test_settings: Settings) -> AsyncIterator[FastAPI]:
    application = create_app(test_settings)
    async with application.router.lifespan_context(application):
        yield application


@asynccontextmanager
async def isolated_client(
    app: FastAPI, headers: dict[str, str] | None = None
) -> AsyncIterator[AsyncClient]:
    async with app.state.engine.connect() as connection:
        transaction = await connection.begin()
        factory = async_sessionmaker(
            bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
        )

        async def isolated_session() -> AsyncIterator[AsyncSession]:
            async with factory() as session:
                yield session

        app.dependency_overrides[get_session] = isolated_session
        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url=BASE_URL, headers=headers) as http:
            yield http
        app.dependency_overrides.clear()
        await transaction.rollback()


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with isolated_client(app, {"Authorization": f"Bearer {token_for()}"}) as http:
        yield http


@pytest.fixture
async def anonymous(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with isolated_client(app) as http:
        yield http

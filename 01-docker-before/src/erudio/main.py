from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from erudio.core.config import Settings, get_settings
from erudio.core.database import create_engine, create_session_factory
from erudio.core.error_handlers import register_error_handlers
from erudio.core.limits import RequestSizeLimitMiddleware
from erudio.core.logs import configure_logging
from erudio.core.openapi import install_error_docs
from erudio.core.storage import create_s3_client
from erudio.routers import auth, book, email, file, person, test_log
from erudio.services.file_storage import ensure_bucket

TERMS_AND_LICENSE = "https://pub.erudio.com.br/meus-cursos"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    engine = create_engine(app.state.settings)
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)
    app.state.s3_client = create_s3_client(app.state.settings)
    await ensure_bucket(
        app.state.s3_client, app.state.settings.aws_s3_bucket, app.state.settings.aws_s3_region
    )
    try:
        yield
    finally:
        await engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(
        title="REST API with FastAPI and Python",
        version="v1",
        description="Erudio REST API (People, Books, Auth, Files, e-Mail) ported from Java.",
        terms_of_service=TERMS_AND_LICENSE,
        license_info={"name": "Apache 2.0", "url": TERMS_AND_LICENSE},
        openapi_tags=[
            {
                "name": "Authentication Endpoint!",
                "description": "Sign in, refresh and create users",
            },
            {"name": "People", "description": "Endpoints for Managing People"},
            {"name": "Book", "description": "Endpoints for Managing Book"},
            {"name": "File Endpoint", "description": "Upload and download files"},
            {"name": "Email Endpoint", "description": "Send e-mails, with or without attachment"},
            {"name": "Test Log", "description": "Generates one log line per level"},
        ],
        docs_url="/swagger-ui/index.html",
        redoc_url=None,
        openapi_url="/v3/api-docs",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    app.add_middleware(
        RequestSizeLimitMiddleware, max_bytes=settings.max_request_size_mb * 1024 * 1024
    )
    register_error_handlers(app)
    app.include_router(auth.router)
    app.include_router(person.router)
    app.include_router(book.router)
    app.include_router(file.router)
    app.include_router(email.router)
    app.include_router(test_log.router)
    install_error_docs(app)
    return app

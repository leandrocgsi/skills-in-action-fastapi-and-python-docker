from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

MIN_SECRET_BYTES = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    jwt_secret_key: str
    jwt_expire_milliseconds: int = 3_600_000
    cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:8080",
        "http://localhost:3000",
        "https://www.erudio.com.br",
    ]
    aws_s3_bucket: str = "erudio-files"
    aws_s3_region: str = "us-east-1"
    aws_s3_endpoint: str | None = "http://localhost:4566"
    aws_s3_access_key: str | None = "test"
    aws_s3_secret_key: str | None = "test"  # noqa: S105 -- LocalStack's fixed dev credential
    max_file_size_mb: int = 200
    max_request_size_mb: int = 215
    mail_host: str = "smtp.gmail.com"
    mail_port: int = 587
    mail_starttls: bool = True
    email_username: str | None = None
    email_password: str | None = Field(default=None, repr=False)
    email_default_subject: str = "Default Subject"
    email_default_message: str = "Default Message"
    log_level: str = "INFO"
    db_pool_size: int = 10
    db_max_overflow: int = 10
    db_pool_recycle_seconds: int = 1800

    @field_validator(
        "email_username",
        "email_password",
        "aws_s3_endpoint",
        "aws_s3_access_key",
        "aws_s3_secret_key",
        mode="before",
    )
    @classmethod
    def blank_is_unset(cls, value: object) -> object:
        return None if isinstance(value, str) and not value.strip() else value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("jwt_secret_key")
    @classmethod
    def long_enough_secret(cls, value: str) -> str:
        if len(value.encode()) < MIN_SECRET_BYTES:
            msg = f"JWT_SECRET_KEY must have at least {MIN_SECRET_BYTES} bytes"
            raise ValueError(msg)
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()

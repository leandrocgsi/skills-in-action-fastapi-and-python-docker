from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, PlainSerializer
from pydantic.alias_generators import to_camel

from erudio.core.timeutil import format_timestamp


def _not_blank(value: str) -> str:
    if not value.strip():
        msg = "must not be blank"
        raise ValueError(msg)
    return value


NonBlank = Annotated[
    str,
    AfterValidator(_not_blank),
    Field(json_schema_extra={"minLength": 1, "pattern": r"\S"}),
]
Timestamp = Annotated[datetime, PlainSerializer(format_timestamp, return_type=str)]


class CredentialsRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    username: NonBlank
    password: NonBlank
    fullname: str | None = None


class AccountCredentialsResponse(BaseModel):
    username: str
    password: str
    fullname: str | None


class TokenResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, validate_by_name=True)

    username: str
    authenticated: bool
    created: Timestamp
    expiration: Timestamp
    access_token: str
    refresh_token: str

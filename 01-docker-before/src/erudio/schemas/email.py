from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class EmailRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    to: Annotated[str, Field(min_length=1)]
    subject: str | None = None
    body: str | None = None


class StrictEmailRequest(EmailRequest):
    """The `emailRequest` part of the multipart endpoint rejects unknown properties."""

    model_config = ConfigDict(extra="forbid")

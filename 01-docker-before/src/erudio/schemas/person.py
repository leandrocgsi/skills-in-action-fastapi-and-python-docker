from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

FirstName = Annotated[str, Field(max_length=80)]
LastName = Annotated[str, Field(max_length=80)]
Address = Annotated[str, Field(max_length=100)]
Gender = Annotated[str, Field(max_length=6)]
Url = Annotated[str | None, Field(max_length=255)]


class PersonCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, validate_by_name=True, extra="ignore")

    first_name: FirstName
    last_name: LastName
    address: Address
    gender: Gender
    enabled: bool
    profile_url: Url = None
    photo_url: Url = None


class PersonUpdate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, validate_by_name=True, extra="ignore")

    id: int
    first_name: FirstName
    last_name: LastName
    address: Address
    gender: Gender


class PersonResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, validate_by_name=True, from_attributes=True)

    id: int
    first_name: str
    last_name: str
    address: str
    gender: str
    enabled: bool
    profile_url: str | None
    photo_url: str | None

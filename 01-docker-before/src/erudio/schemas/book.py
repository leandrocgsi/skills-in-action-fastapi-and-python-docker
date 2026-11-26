from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from erudio.schemas.types import LocalDate, Money


class BookCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, validate_by_name=True, extra="ignore")

    author: str
    launch_date: LocalDate
    price: Money
    title: str


class BookUpdate(BookCreate):
    id: int


class BookResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, validate_by_name=True, from_attributes=True)

    id: int
    author: str
    launch_date: LocalDate
    price: Money
    title: str

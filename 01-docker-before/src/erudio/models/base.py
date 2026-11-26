from datetime import date, datetime, time
from typing import Any

from sqlalchemy import DateTime
from sqlalchemy.dialects import mysql
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import TypeDecorator


class Base(DeclarativeBase):
    pass


class LocalDate(TypeDecorator[date]):
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: date | None, dialect: Dialect) -> Any:
        return None if value is None else datetime.combine(value, time.min)

    def process_result_value(self, value: Any, dialect: Dialect) -> date | None:
        return None if value is None else value.date()


class BitBool(TypeDecorator[bool]):
    impl = mysql.BIT(1)
    cache_ok = True

    def process_bind_param(self, value: bool | None, dialect: Dialect) -> Any:
        return None if value is None else int(value)

    def process_result_value(self, value: Any, dialect: Dialect) -> bool | None:
        if value is None:
            return None
        if isinstance(value, bytes | bytearray):
            return int.from_bytes(value, "big") != 0
        return bool(value)

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any

from pydantic import BeforeValidator, Field, PlainSerializer

_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _parse_local_date(value: Any) -> date:
    if isinstance(value, datetime):
        msg = "Expected a date (yyyy-MM-dd), got a date-time"
        raise ValueError(msg)
    if isinstance(value, date):
        return value
    if isinstance(value, str) and _ISO_DATE.match(value):
        return date.fromisoformat(value)
    msg = "Expected a date in the yyyy-MM-dd format"
    raise ValueError(msg)


LocalDate = Annotated[date, BeforeValidator(_parse_local_date)]
# DECIMAL(65, 2) holds 63 integer digits.
Money = Annotated[
    Decimal,
    Field(gt=-(10**63), lt=10**63 - 1),
    PlainSerializer(float, return_type=float, when_used="json"),
]

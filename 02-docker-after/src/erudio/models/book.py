from datetime import date
from decimal import Decimal

from sqlalchemy import Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from erudio.models.base import Base, LocalDate


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    author: Mapped[str] = mapped_column(Text)
    launch_date: Mapped[date] = mapped_column(LocalDate)
    price: Mapped[Decimal] = mapped_column(Numeric(65, 2))
    title: Mapped[str] = mapped_column(Text)

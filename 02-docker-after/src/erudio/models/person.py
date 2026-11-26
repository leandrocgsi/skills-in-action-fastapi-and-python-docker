from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from erudio.models.base import Base, BitBool


class Person(Base):
    __tablename__ = "person"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80))
    address: Mapped[str] = mapped_column(String(100))
    gender: Mapped[str] = mapped_column(String(6))
    enabled: Mapped[bool] = mapped_column(BitBool)
    profile_url: Mapped[str | None] = mapped_column("wikipedia_profile_url", String(255))
    photo_url: Mapped[str | None] = mapped_column(String(255))

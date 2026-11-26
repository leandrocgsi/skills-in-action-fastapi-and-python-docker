from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from erudio.models.base import Base, BitBool

user_permission = Table(
    "user_permission",
    Base.metadata,
    Column("id_user", ForeignKey("users.id"), primary_key=True),
    Column("id_permission", ForeignKey("permission.id"), primary_key=True),
)


class Permission(Base):
    __tablename__ = "permission"

    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str | None] = mapped_column(String(255))


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_name: Mapped[str] = mapped_column(String(255), unique=True)
    full_name: Mapped[str | None] = mapped_column(String(255))
    password: Mapped[str] = mapped_column(String(255))
    account_non_expired: Mapped[bool | None] = mapped_column(BitBool)
    account_non_locked: Mapped[bool | None] = mapped_column(BitBool)
    credentials_non_expired: Mapped[bool | None] = mapped_column(BitBool)
    enabled: Mapped[bool | None] = mapped_column(BitBool)
    permissions: Mapped[list[Permission]] = relationship(
        secondary=user_permission, lazy="selectin", order_by=Permission.id
    )

    @property
    def roles(self) -> list[str]:
        return [permission.description for permission in self.permissions if permission.description]

    @property
    def is_active(self) -> bool:
        flags = (
            self.enabled,
            self.account_non_expired,
            self.account_non_locked,
            self.credentials_non_expired,
        )
        return all(flag is True for flag in flags)

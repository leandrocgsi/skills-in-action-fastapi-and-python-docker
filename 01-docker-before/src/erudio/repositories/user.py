from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from erudio.models.user import User


async def get_by_username(session: AsyncSession, username: str) -> User | None:
    result = await session.scalars(select(User).where(User.user_name == username))
    return result.first()


def add(session: AsyncSession, user: User) -> None:
    session.add(user)

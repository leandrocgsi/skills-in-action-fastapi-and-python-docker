from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from erudio.models.book import Book


async def get(session: AsyncSession, book_id: int) -> Book | None:
    return await session.get(Book, book_id)


async def list_page(
    session: AsyncSession, *, offset: int, limit: int, descending: bool
) -> Sequence[Book]:
    order = (Book.title.desc(), Book.id.desc()) if descending else (Book.title.asc(), Book.id.asc())
    result = await session.scalars(select(Book).order_by(*order).offset(offset).limit(limit))
    return result.all()


async def count(session: AsyncSession) -> int:
    return await session.scalar(select(func.count()).select_from(Book)) or 0

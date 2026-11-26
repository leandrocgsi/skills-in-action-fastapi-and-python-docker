from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from erudio.core.errors import ResourceNotFoundError
from erudio.models.book import Book
from erudio.repositories import book as books
from erudio.schemas.book import BookCreate, BookUpdate


async def list_books(
    session: AsyncSession, *, page: int, size: int, descending: bool
) -> tuple[Sequence[Book], int]:
    items = await books.list_page(session, offset=page * size, limit=size, descending=descending)
    return items, await books.count(session)


async def get_book(session: AsyncSession, book_id: int) -> Book:
    book = await books.get(session, book_id)
    if book is None:
        raise ResourceNotFoundError
    return book


async def create_book(session: AsyncSession, payload: BookCreate) -> Book:
    book = Book(**payload.model_dump())
    session.add(book)
    await session.commit()
    await session.refresh(book)
    return book


async def update_book(session: AsyncSession, payload: BookUpdate) -> Book:
    book = await get_book(session, payload.id)
    book.author = payload.author
    book.launch_date = payload.launch_date
    book.price = payload.price
    book.title = payload.title
    await session.commit()
    await session.refresh(book)
    return book


async def delete_book(session: AsyncSession, book_id: int) -> None:
    book = await get_book(session, book_id)
    await session.delete(book)
    await session.commit()

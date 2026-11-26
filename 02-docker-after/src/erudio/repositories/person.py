from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from erudio.models.person import Person


async def get(session: AsyncSession, person_id: int) -> Person | None:
    return await session.get(Person, person_id)


async def list_page(
    session: AsyncSession, *, offset: int, limit: int, descending: bool, name: str | None = None
) -> Sequence[Person]:
    order = (
        (Person.first_name.desc(), Person.id.desc())
        if descending
        else (Person.first_name.asc(), Person.id.asc())
    )
    query = select(Person)
    if name is not None:
        query = query.where(Person.first_name.icontains(name, autoescape=True))
    result = await session.scalars(query.order_by(*order).offset(offset).limit(limit))
    return result.all()


async def count(session: AsyncSession, name: str | None = None) -> int:
    query = select(func.count()).select_from(Person)
    if name is not None:
        query = query.where(Person.first_name.icontains(name, autoescape=True))
    return await session.scalar(query) or 0

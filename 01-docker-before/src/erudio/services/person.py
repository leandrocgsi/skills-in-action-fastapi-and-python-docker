from collections.abc import Sequence
from pathlib import PurePath

import anyio.to_thread
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from erudio.core.errors import BadRequestError, ResourceNotFoundError
from erudio.files.importers import IMPORTERS, FileProcessingError
from erudio.models.person import Person
from erudio.repositories import person as people
from erudio.schemas.person import PersonCreate, PersonUpdate


async def list_people(
    session: AsyncSession, *, page: int, size: int, descending: bool, name: str | None = None
) -> tuple[Sequence[Person], int]:
    items = await people.list_page(
        session, offset=page * size, limit=size, descending=descending, name=name
    )
    return items, await people.count(session, name)


async def get_person(session: AsyncSession, person_id: int) -> Person:
    person = await people.get(session, person_id)
    if person is None:
        raise ResourceNotFoundError
    return person


async def create_person(session: AsyncSession, payload: PersonCreate) -> Person:
    person = Person(**payload.model_dump())
    session.add(person)
    await session.commit()
    await session.refresh(person)
    return person


async def update_person(session: AsyncSession, payload: PersonUpdate) -> Person:
    person = await get_person(session, payload.id)
    person.first_name = payload.first_name
    person.last_name = payload.last_name
    person.address = payload.address
    person.gender = payload.gender
    await session.commit()
    await session.refresh(person)
    return person


async def disable_person(session: AsyncSession, person_id: int) -> Person:
    person = await get_person(session, person_id)
    person.enabled = False
    await session.commit()
    await session.refresh(person)
    return person


async def delete_person(session: AsyncSession, person_id: int) -> None:
    person = await get_person(session, person_id)
    await session.delete(person)
    await session.commit()


async def import_people(
    session: AsyncSession, filename: str | None, content: bytes
) -> list[Person]:
    if not content:
        raise BadRequestError("Please set a Valid File!")
    if not filename:
        raise BadRequestError("File name cannot be null")
    importer = IMPORTERS.get(PurePath(filename).suffix.lower())
    if importer is None:
        raise BadRequestError("Invalid File Format!")
    try:
        rows = await anyio.to_thread.run_sync(importer, content)
    except (FileProcessingError, ValidationError) as error:
        raise BadRequestError("Error processing the file!") from error
    created = [Person(**row.model_dump()) for row in rows]
    session.add_all(created)
    await session.commit()
    for person in created:
        await session.refresh(person)
    return created

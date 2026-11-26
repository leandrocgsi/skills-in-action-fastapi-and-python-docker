from urllib.parse import quote

from fastapi import APIRouter, Depends, Request, Response, UploadFile

from erudio.core.auth import current_user
from erudio.core.database import SessionDep
from erudio.core.errors import NotAcceptableError
from erudio.core.hypermedia.models import Link, Page, Resource, ResourceList
from erudio.core.hypermedia.pagination import PageParam, SizeParam, page_info, page_links
from erudio.core.negotiation.docs import (
    body_docs,
    item_responses,
    list_responses,
    page_responses,
)
from erudio.core.negotiation.media import select_offered
from erudio.core.negotiation.responder import RespondDep
from erudio.core.negotiation.route import NegotiatingRoute
from erudio.core.openapi import exception_docs
from erudio.files.exporters import EXPORTERS
from erudio.models.person import Person
from erudio.schemas.person import PersonCreate, PersonResponse, PersonUpdate
from erudio.services import person as person_service

router = APIRouter(
    prefix="/api/person/v1",
    tags=["People"],
    route_class=NegotiatingRoute,
    dependencies=[Depends(current_user)],
)

DEFAULT_QUERY = "?page=1&size=12&direction=asc"


def _links(request: Request, person_id: int) -> list[Link]:
    base = str(request.url_for("list_people"))
    own = str(request.url_for("get_person", person_id=person_id))
    return [
        Link("findAll", base + DEFAULT_QUERY, "GET"),
        Link("findByName", f"{base}/findPeopleByName/{DEFAULT_QUERY}", "GET"),
        Link("self", own, "GET"),
        Link("create", base, "POST"),
        Link("massCreation", str(request.url_for("import_people")), "POST"),
        Link("update", base, "PUT"),
        Link("disable", own, "PATCH"),
        Link("delete", own, "DELETE"),
        Link(
            "exportPage",
            str(request.url_for("export_people")) + DEFAULT_QUERY,
            "GET",
            "Export People",
        ),
    ]


def _resource(request: Request, person: Person) -> Resource:
    data = PersonResponse.model_validate(person).model_dump(mode="json", by_alias=True)
    return Resource("PersonDTO", data, _links(request, person.id))


def _page(
    request: Request,
    people: list[Person],
    total: int,
    number: int,
    size: int,
    descending: bool,
    base: str,
) -> Page:
    info = page_info(number, size, total)
    links = page_links(
        request.url.replace(query="", path=base), info, "desc" if descending else "asc"
    )
    return Page("people", [_resource(request, person) for person in people], links, info)


@router.get(
    "",
    summary="Finds all People",
    description="Finds all People, paged and sorted by first name.",
    response_model=None,
    responses=page_responses(PersonResponse, "people"),
)
async def list_people(
    request: Request,
    session: SessionDep,
    respond: RespondDep,
    page: PageParam = 0,
    size: SizeParam = 12,
    direction: str = "asc",
) -> Response:
    descending = direction.lower() == "desc"
    people, total = await person_service.list_people(
        session, page=page, size=size, descending=descending
    )
    base = request.url_for("list_people").path
    return respond(_page(request, list(people), total, page, size, descending, base))


@router.get(
    "/exportPage",
    summary="Exports a page of People as CSV or XLSX",
    description="Send Accept: text/csv or the XLSX media type to choose the file format.",
    response_model=None,
    responses={200: {"description": "The file", "content": {media: {} for media in EXPORTERS}}},
)
async def export_people(
    request: Request,
    session: SessionDep,
    page: PageParam = 0,
    size: SizeParam = 12,
    direction: str = "asc",
) -> Response:
    media = select_offered(request.headers.get("accept"), list(EXPORTERS))
    if media is None:
        raise NotAcceptableError(list(EXPORTERS))
    extension, exporter = EXPORTERS[media]
    people, _ = await person_service.list_people(
        session, page=page, size=size, descending=direction.lower() == "desc"
    )
    content = exporter([PersonResponse.model_validate(person) for person in people])
    return Response(
        content=content,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="people_exported{extension}"'},
    )


@router.get(
    "/findPeopleByName/{first_name}",
    summary="Finds People by first name",
    description="Finds the People whose first name contains the text, paged.",
    response_model=None,
    responses=page_responses(PersonResponse, "people"),
)
async def search_people(
    request: Request,
    session: SessionDep,
    respond: RespondDep,
    first_name: str,
    page: PageParam = 0,
    size: SizeParam = 12,
    direction: str = "asc",
) -> Response:
    descending = direction.lower() == "desc"
    people, total = await person_service.list_people(
        session, page=page, size=size, descending=descending, name=first_name
    )
    base = f"{request.url_for('list_people').path}/findPeopleByName/{quote(first_name, safe='')}"
    return respond(_page(request, list(people), total, page, size, descending, base))


@router.get(
    "/{person_id}",
    summary="Finds a Person",
    response_model=None,
    responses=item_responses(PersonResponse),
)
async def get_person(
    request: Request, session: SessionDep, respond: RespondDep, person_id: int
) -> Response:
    return respond(_resource(request, await person_service.get_person(session, person_id)))


@router.post(
    "",
    summary="Adds a new Person",
    response_model=None,
    responses=item_responses(PersonResponse),
    openapi_extra=body_docs(PersonCreate),
)
async def create_person(
    request: Request, session: SessionDep, respond: RespondDep, payload: PersonCreate
) -> Response:
    return respond(_resource(request, await person_service.create_person(session, payload)))


@router.post(
    "/massCreation",
    summary="Creates many People from a CSV or XLSX file",
    response_model=None,
    responses={
        **list_responses(PersonResponse),
        400: exception_docs("The file is empty, unreadable or not a CSV or XLSX", or_problem=True),
    },
)
async def import_people(
    request: Request, session: SessionDep, respond: RespondDep, file: UploadFile
) -> Response:
    created = await person_service.import_people(session, file.filename, await file.read())
    return respond(ResourceList([_resource(request, person) for person in created]))


@router.put(
    "",
    summary="Updates a Person",
    response_model=None,
    responses=item_responses(PersonResponse),
    openapi_extra=body_docs(PersonUpdate),
)
async def update_person(
    request: Request, session: SessionDep, respond: RespondDep, payload: PersonUpdate
) -> Response:
    return respond(_resource(request, await person_service.update_person(session, payload)))


@router.patch(
    "/{person_id}",
    summary="Disables a Person",
    response_model=None,
    responses=item_responses(PersonResponse),
)
async def disable_person(
    request: Request, session: SessionDep, respond: RespondDep, person_id: int
) -> Response:
    return respond(_resource(request, await person_service.disable_person(session, person_id)))


@router.delete("/{person_id}", summary="Deletes a Person", status_code=204)
async def delete_person(session: SessionDep, person_id: int) -> Response:
    await person_service.delete_person(session, person_id)
    return Response(status_code=204)

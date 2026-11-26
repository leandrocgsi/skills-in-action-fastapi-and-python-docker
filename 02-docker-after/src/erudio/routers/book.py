from fastapi import APIRouter, Depends, Request, Response

from erudio.core.auth import current_user
from erudio.core.database import SessionDep
from erudio.core.hypermedia.models import Link, Page, Resource
from erudio.core.hypermedia.pagination import PageParam, SizeParam, page_info, page_links
from erudio.core.negotiation.docs import body_docs, item_responses, page_responses
from erudio.core.negotiation.responder import RespondDep
from erudio.core.negotiation.route import NegotiatingRoute
from erudio.models.book import Book
from erudio.schemas.book import BookCreate, BookResponse, BookUpdate
from erudio.services import book as book_service

router = APIRouter(
    prefix="/api/book/v1",
    tags=["Book"],
    route_class=NegotiatingRoute,
    dependencies=[Depends(current_user)],
)


def _links(request: Request, book_id: int) -> list[Link]:
    list_url = request.url_for("list_books").include_query_params(page=1, size=12, direction="asc")
    return [
        Link("self", str(request.url_for("get_book", book_id=book_id)), "GET"),
        Link("findAll", str(list_url), "GET"),
        Link("create", str(request.url_for("create_book")), "POST"),
        Link("update", str(request.url_for("update_book")), "PUT"),
        Link("delete", str(request.url_for("delete_book", book_id=book_id)), "DELETE"),
    ]


def _resource(request: Request, book: Book) -> Resource:
    data = BookResponse.model_validate(book).model_dump(mode="json", by_alias=True)
    return Resource("BookDTO", data, _links(request, book.id))


@router.get(
    "",
    summary="Finds all Books",
    description="Finds all Books, paged and sorted by title.",
    response_model=None,
    responses=page_responses(BookResponse, "books"),
)
async def list_books(
    request: Request,
    session: SessionDep,
    respond: RespondDep,
    page: PageParam = 0,
    size: SizeParam = 12,
    direction: str = "asc",
) -> Response:
    descending = direction.lower() == "desc"
    books, total = await book_service.list_books(
        session, page=page, size=size, descending=descending
    )
    info = page_info(page, size, total)
    links = page_links(request.url_for("list_books"), info, "desc" if descending else "asc")
    return respond(Page("books", [_resource(request, book) for book in books], links, info))


@router.get(
    "/{book_id}",
    summary="Finds a Book",
    response_model=None,
    responses=item_responses(BookResponse),
)
async def get_book(
    request: Request, session: SessionDep, respond: RespondDep, book_id: int
) -> Response:
    return respond(_resource(request, await book_service.get_book(session, book_id)))


@router.post(
    "",
    summary="Adds a new Book",
    response_model=None,
    responses=item_responses(BookResponse),
    openapi_extra=body_docs(BookCreate),
)
async def create_book(
    request: Request, session: SessionDep, respond: RespondDep, payload: BookCreate
) -> Response:
    return respond(_resource(request, await book_service.create_book(session, payload)))


@router.put(
    "",
    summary="Updates a Book",
    response_model=None,
    responses=item_responses(BookResponse),
    openapi_extra=body_docs(BookUpdate),
)
async def update_book(
    request: Request, session: SessionDep, respond: RespondDep, payload: BookUpdate
) -> Response:
    return respond(_resource(request, await book_service.update_book(session, payload)))


@router.delete("/{book_id}", summary="Deletes a Book", status_code=204)
async def delete_book(session: SessionDep, book_id: int) -> Response:
    await book_service.delete_book(session, book_id)
    return Response(status_code=204)

from typing import Annotated

from fastapi import APIRouter, Header, Request, Response

from erudio.core.database import SessionDep
from erudio.core.dependencies import SettingsDep, issuer_of
from erudio.core.hypermedia.models import Plain
from erudio.core.negotiation.docs import body_docs, item_responses
from erudio.core.negotiation.responder import RespondDep
from erudio.core.negotiation.route import NegotiatingRoute
from erudio.core.openapi import exception_docs
from erudio.schemas.auth import AccountCredentialsResponse, CredentialsRequest, TokenResponse
from erudio.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["Authentication Endpoint!"], route_class=NegotiatingRoute)


@router.post(
    "/signin",
    name="auth_signin",
    summary="Authenticates a user and returns a token",
    response_model=None,
    responses={**item_responses(TokenResponse), 401: exception_docs("Bad credentials")},
    openapi_extra=body_docs(CredentialsRequest),
)
async def signin(
    request: Request,
    session: SessionDep,
    settings: SettingsDep,
    respond: RespondDep,
    credentials: CredentialsRequest,
) -> Response:
    token = await auth_service.sign_in(session, settings, credentials, issuer_of(request))
    return respond(Plain("TokenDTO", token.model_dump(mode="json", by_alias=True)))


@router.put(
    "/refresh/{username}",
    name="auth_refresh",
    summary="Refreshes the token of a user",
    response_model=None,
    responses={
        **item_responses(TokenResponse),
        401: exception_docs("Invalid or expired refresh token"),
        403: exception_docs("The token belongs to another user"),
        404: exception_docs("Unknown user"),
    },
)
async def refresh(
    request: Request,
    session: SessionDep,
    settings: SettingsDep,
    respond: RespondDep,
    username: str,
    authorization: Annotated[str, Header(description="Bearer <refreshToken>")],
) -> Response:
    token = await auth_service.refresh(
        session, settings, username, authorization, issuer_of(request)
    )
    return respond(Plain("TokenDTO", token.model_dump(mode="json", by_alias=True)))


@router.post(
    "/createUser",
    name="auth_create_user",
    summary="Creates a new user",
    response_model=None,
    responses={
        **item_responses(AccountCredentialsResponse),
        409: exception_docs("The username is already taken"),
    },
    openapi_extra=body_docs(CredentialsRequest),
)
async def create_user(
    session: SessionDep, respond: RespondDep, credentials: CredentialsRequest
) -> Response:
    user = await auth_service.create_user(session, credentials)
    created = AccountCredentialsResponse(
        username=user.user_name, password=user.password, fullname=user.full_name
    )
    return respond(Plain("AccountCredentialsDTO", created.model_dump()))

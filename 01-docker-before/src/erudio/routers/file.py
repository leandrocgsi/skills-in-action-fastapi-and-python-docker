import mimetypes
from typing import TYPE_CHECKING, Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Request, Response, UploadFile

from erudio.core.auth import current_user
from erudio.core.config import Settings
from erudio.core.dependencies import SettingsDep
from erudio.core.hypermedia.models import Plain, PlainList
from erudio.core.negotiation.docs import item_responses, list_responses
from erudio.core.negotiation.responder import RespondDep
from erudio.core.negotiation.route import NegotiatingRoute
from erudio.core.openapi import exception_docs
from erudio.core.storage import S3ClientDep
from erudio.schemas.file import UploadFileResponse
from erudio.services import file_storage

if TYPE_CHECKING:
    from types_boto3_s3 import S3Client
else:
    S3Client = object

# The built-in table only: the system one (Windows registry, /etc/mime.types) varies by host.
MIME_TYPES = mimetypes.MimeTypes()

router = APIRouter(
    prefix="/api/file/v1",
    tags=["File Endpoint"],
    route_class=NegotiatingRoute,
    dependencies=[Depends(current_user)],
)


def _content_disposition(filename: str) -> str:
    encoded = quote(filename)
    if encoded != filename:
        return f"attachment; filename*=utf-8''{encoded}"
    return f'attachment; filename="{filename}"'


async def _store(
    request: Request, settings: Settings, s3_client: S3Client, upload: UploadFile
) -> dict[str, object]:
    name = await file_storage.store(
        s3_client,
        settings.aws_s3_bucket,
        upload.filename,
        upload.file,
        upload.size or 0,
        settings.max_file_size_mb * 1024 * 1024,
        upload.content_type,
    )
    return UploadFileResponse(
        file_name=name,
        file_download_uri=f"{str(request.base_url).rstrip('/')}/api/file/v1/downloadFile/"
        f"{quote(name)}",
        file_type=upload.content_type or None,
        size=upload.size or 0,
    ).model_dump(by_alias=True)


@router.post(
    "/uploadFile",
    name="file_upload",
    summary="Uploads a file",
    response_model=None,
    responses={
        **item_responses(UploadFileResponse),
        400: exception_docs("The file name is not accepted", or_problem=True),
    },
)
async def upload_file(
    request: Request,
    settings: SettingsDep,
    s3_client: S3ClientDep,
    respond: RespondDep,
    file: UploadFile,
) -> Response:
    return respond(Plain("UploadFileResponseDTO", await _store(request, settings, s3_client, file)))


@router.post(
    "/uploadMultipleFiles",
    name="file_upload_multiple",
    summary="Uploads multiple files",
    response_model=None,
    responses={
        **list_responses(UploadFileResponse),
        400: exception_docs("A file name is not accepted", or_problem=True),
    },
)
async def upload_multiple_files(
    request: Request,
    settings: SettingsDep,
    s3_client: S3ClientDep,
    respond: RespondDep,
    files: Annotated[list[UploadFile], File(min_length=1)],
) -> Response:
    return respond(
        PlainList([await _store(request, settings, s3_client, upload) for upload in files])
    )


@router.get(
    "/downloadFile/{file_name}",
    name="file_download",
    summary="Downloads a file",
    response_model=None,
    responses={
        200: {"description": "The file", "content": {"application/octet-stream": {}}},
        404: exception_docs("File not found"),
    },
)
async def download_file(settings: SettingsDep, s3_client: S3ClientDep, file_name: str) -> Response:
    content = await file_storage.locate(s3_client, settings.aws_s3_bucket, file_name)
    media_type = MIME_TYPES.guess_type(file_name)[0] or "application/octet-stream"
    return Response(
        content=content,
        media_type=media_type,
        headers={"content-disposition": _content_disposition(file_name)},
    )

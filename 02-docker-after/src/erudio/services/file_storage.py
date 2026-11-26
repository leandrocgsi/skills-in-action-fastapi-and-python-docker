import logging
from typing import TYPE_CHECKING, BinaryIO, cast

import anyio.to_thread
from botocore.exceptions import ClientError

from erudio.core.errors import BadRequestError, PayloadTooLargeError, StoredFileNotFoundError

if TYPE_CHECKING:
    from types_boto3_s3 import S3Client
    from types_boto3_s3.literals import BucketLocationConstraintType
else:
    S3Client = object
    BucketLocationConstraintType = str

logger = logging.getLogger(__name__)

FORBIDDEN = ("..", "/", "\\", "\0")

US_EAST_1 = "us-east-1"


def _is_plain_name(name: str) -> bool:
    return bool(name) and name != "." and not any(part in name for part in FORBIDDEN)


def _error_code(error: ClientError) -> str | None:
    return error.response.get("Error", {}).get("Code")


def _create_bucket(s3_client: S3Client, bucket: str, region: str) -> None:
    if region == US_EAST_1:
        s3_client.create_bucket(Bucket=bucket)
    else:
        constraint = cast(BucketLocationConstraintType, region)
        s3_client.create_bucket(
            Bucket=bucket, CreateBucketConfiguration={"LocationConstraint": constraint}
        )


def _ensure_bucket(s3_client: S3Client, bucket: str, region: str) -> None:
    try:
        s3_client.head_bucket(Bucket=bucket)
    except ClientError as error:
        if _error_code(error) not in ("404", "NoSuchBucket"):
            raise
        logger.info("Creating S3 bucket %s", bucket)
        _create_bucket(s3_client, bucket, region)


async def ensure_bucket(s3_client: S3Client, bucket: str, region: str) -> None:
    await anyio.to_thread.run_sync(_ensure_bucket, s3_client, bucket, region)


def _put_object(
    s3_client: S3Client, bucket: str, name: str, source: BinaryIO, size: int, content_type: str
) -> None:
    s3_client.put_object(
        Bucket=bucket, Key=name, Body=source, ContentLength=size, ContentType=content_type
    )


async def store(
    s3_client: S3Client,
    bucket: str,
    filename: str | None,
    source: BinaryIO,
    size: int,
    max_bytes: int,
    content_type: str | None = None,
) -> str:
    name = filename or ""
    if size > max_bytes:
        raise PayloadTooLargeError
    if not _is_plain_name(name):
        logger.error("Sorry! Filename Contains a Invalid path Sequence %s", name)
        raise BadRequestError(f"Could not store file {name}. Please try Again!")
    resolved_type = content_type or "application/octet-stream"
    await anyio.to_thread.run_sync(
        _put_object, s3_client, bucket, name, source, size, resolved_type
    )
    return name


def _get_object(s3_client: S3Client, bucket: str, filename: str) -> bytes:
    body = s3_client.get_object(Bucket=bucket, Key=filename)["Body"]
    return body.read()


async def locate(s3_client: S3Client, bucket: str, filename: str) -> bytes:
    if not _is_plain_name(filename):
        logger.error("File not found %s", filename)
        raise StoredFileNotFoundError(f"File not found {filename}")
    try:
        return await anyio.to_thread.run_sync(_get_object, s3_client, bucket, filename)
    except ClientError as error:
        if _error_code(error) not in ("404", "NoSuchKey"):
            raise
        logger.error("File not found %s", filename)
        raise StoredFileNotFoundError(f"File not found {filename}") from error

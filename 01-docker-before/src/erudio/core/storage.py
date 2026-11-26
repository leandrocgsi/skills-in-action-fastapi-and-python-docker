from typing import TYPE_CHECKING, Annotated

import boto3
from fastapi import Depends, Request

from erudio.core.config import Settings

if TYPE_CHECKING:
    from types_boto3_s3 import S3Client
else:
    S3Client = object


def create_s3_client(settings: Settings) -> S3Client:
    if settings.aws_s3_endpoint:
        return boto3.client(
            "s3",
            region_name=settings.aws_s3_region,
            endpoint_url=settings.aws_s3_endpoint,
            aws_access_key_id=settings.aws_s3_access_key,
            aws_secret_access_key=settings.aws_s3_secret_key,
        )
    return boto3.client("s3", region_name=settings.aws_s3_region)


def get_s3_client(request: Request) -> S3Client:
    client: S3Client = request.app.state.s3_client
    return client


S3ClientDep = Annotated[S3Client, Depends(get_s3_client)]

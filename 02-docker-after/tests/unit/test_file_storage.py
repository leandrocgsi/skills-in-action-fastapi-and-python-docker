import io
from typing import cast
from unittest.mock import Mock

import pytest
from botocore.exceptions import ClientError
from types_boto3_s3 import S3Client

from erudio.core.errors import BadRequestError, PayloadTooLargeError, StoredFileNotFoundError
from erudio.services import file_storage

UNUSED_CLIENT = cast(S3Client, None)


def client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": "boom"}}, "Operation")


async def test_a_file_over_the_limit_is_refused_before_it_is_written() -> None:
    with pytest.raises(PayloadTooLargeError, match="Maximum upload size exceeded"):
        await file_storage.store(
            UNUSED_CLIENT, "bucket", "big.bin", io.BytesIO(b"x" * 11), 11, max_bytes=10
        )


@pytest.mark.parametrize("name", [None, "", ".", "..", "a/b", "a\\b", "x..y", "nul\0"])
async def test_names_that_are_not_plain_are_refused(name: str | None) -> None:
    with pytest.raises(BadRequestError, match=r"Please try Again!"):
        await file_storage.store(UNUSED_CLIENT, "bucket", name, io.BytesIO(b"x"), 1, max_bytes=10)


@pytest.mark.parametrize("name", ["", ".", "..", "a/b", "a\\b", "nul\0"])
async def test_locate_refuses_a_name_that_is_not_plain(name: str) -> None:
    with pytest.raises(StoredFileNotFoundError, match=r"File not found"):
        await file_storage.locate(UNUSED_CLIENT, "bucket", name)


async def test_locate_turns_a_missing_key_into_a_not_found_error() -> None:
    broken = Mock(spec=S3Client)
    broken.get_object.side_effect = client_error("NoSuchKey")

    with pytest.raises(StoredFileNotFoundError, match=r"File not found missing\.txt"):
        await file_storage.locate(broken, "bucket", "missing.txt")


async def test_locate_lets_an_unexpected_s3_error_propagate() -> None:
    broken = Mock(spec=S3Client)
    broken.get_object.side_effect = client_error("500")

    with pytest.raises(ClientError):
        await file_storage.locate(broken, "bucket", "a.txt")


async def test_ensure_bucket_creates_it_when_missing() -> None:
    absent = Mock(spec=S3Client)
    absent.head_bucket.side_effect = client_error("404")

    await file_storage.ensure_bucket(absent, "bucket", "us-east-1")

    absent.create_bucket.assert_called_once_with(Bucket="bucket")


async def test_ensure_bucket_sets_a_location_constraint_outside_us_east_1() -> None:
    absent = Mock(spec=S3Client)
    absent.head_bucket.side_effect = client_error("NoSuchBucket")

    await file_storage.ensure_bucket(absent, "bucket", "eu-west-1")

    absent.create_bucket.assert_called_once_with(
        Bucket="bucket", CreateBucketConfiguration={"LocationConstraint": "eu-west-1"}
    )


async def test_ensure_bucket_does_nothing_when_it_already_exists() -> None:
    present = Mock(spec=S3Client)

    await file_storage.ensure_bucket(present, "bucket", "us-east-1")

    present.create_bucket.assert_not_called()


async def test_ensure_bucket_lets_an_unexpected_s3_error_propagate() -> None:
    broken = Mock(spec=S3Client)
    broken.head_bucket.side_effect = client_error("403")

    with pytest.raises(ClientError):
        await file_storage.ensure_bucket(broken, "bucket", "us-east-1")

    broken.create_bucket.assert_not_called()

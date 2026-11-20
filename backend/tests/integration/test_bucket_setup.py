"""Criterion 1 regression: two API processes starting on a fresh store both come up."""

import asyncio
import uuid

from types_aiobotocore_s3 import S3Client

from app.storage.s3_object_storage import S3ObjectStorage


async def test_concurrent_ensure_bucket_on_a_fresh_store_both_succeed(s3: S3Client) -> None:
    bucket = f"race-{uuid.uuid4().hex[:12]}"
    first, second = S3ObjectStorage(s3, bucket), S3ObjectStorage(s3, bucket)

    try:
        await asyncio.gather(*(storage.ensure_bucket() for storage in [first, second] * 3))

        assert await first.is_ready() is True
        rules = (await s3.get_bucket_lifecycle_configuration(Bucket=bucket))["Rules"]
        assert [rule["Expiration"]["Days"] for rule in rules] == [7]
    finally:
        await s3.delete_bucket(Bucket=bucket)


async def test_ensure_bucket_twice_in_a_row_is_a_no_op(s3: S3Client) -> None:
    bucket = f"again-{uuid.uuid4().hex[:12]}"
    storage = S3ObjectStorage(s3, bucket)

    try:
        await storage.ensure_bucket()
        await storage.ensure_bucket()

        assert await storage.is_ready() is True
    finally:
        await s3.delete_bucket(Bucket=bucket)

"""Read the test bucket and the stream directly, to assert what an upload stored."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from botocore.exceptions import ClientError
from types_aiobotocore_s3 import S3Client

from app.core.settings import Settings
from app.infrastructure import open_s3


@asynccontextmanager
async def bucket_client(settings: Settings) -> AsyncIterator[S3Client]:
    """An S3 client on the test bucket."""
    async with open_s3(settings) as client:
        yield client


async def object_exists(client: S3Client, bucket: str, key: str) -> bool:
    """True when ``key`` is stored."""
    try:
        await client.head_object(Bucket=bucket, Key=key)
    except ClientError:
        return False
    return True


async def object_bytes(client: S3Client, bucket: str, key: str) -> bytes:
    """The stored bytes of ``key``."""
    response = await client.get_object(Bucket=bucket, Key=key)
    async with response["Body"] as stream:
        return await stream.read()

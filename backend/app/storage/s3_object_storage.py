"""``ObjectStorage`` on any S3 API (SeaweedFS locally), through ``aiobotocore``."""

from typing import TYPE_CHECKING

from botocore.exceptions import BotoCoreError, ClientError

if TYPE_CHECKING:
    from types_aiobotocore_s3 import S3Client

RETENTION_DAYS = 7


class S3ObjectStorage:
    """One bucket, whole-object reads and writes, and a 7-day expiry rule (AD-012)."""

    def __init__(self, client: "S3Client", bucket: str) -> None:
        self._client = client
        self._bucket = bucket

    async def ensure_bucket(self) -> None:
        """Create the bucket and its lifecycle rule when missing."""
        try:
            await self._client.head_bucket(Bucket=self._bucket)
        except ClientError:
            await self._client.create_bucket(Bucket=self._bucket)
        await self._client.put_bucket_lifecycle_configuration(
            Bucket=self._bucket,
            LifecycleConfiguration={
                "Rules": [
                    {
                        "ID": "expire-documents",
                        "Status": "Enabled",
                        "Filter": {"Prefix": "documents/"},
                        "Expiration": {"Days": RETENTION_DAYS},
                    }
                ]
            },
        )

    async def put(self, key: str, data: bytes) -> None:
        """Store ``data`` as ``application/pdf``."""
        await self._client.put_object(
            Bucket=self._bucket, Key=key, Body=data, ContentType="application/pdf"
        )

    async def get(self, key: str) -> bytes:
        """Read the whole object."""
        response = await self._client.get_object(Bucket=self._bucket, Key=key)
        async with response["Body"] as stream:
            return await stream.read()

    async def delete(self, key: str) -> None:
        """Delete; S3 treats a missing key as success."""
        await self._client.delete_object(Bucket=self._bucket, Key=key)

    async def is_ready(self) -> bool:
        """True when ``HeadBucket`` succeeds."""
        try:
            await self._client.head_bucket(Bucket=self._bucket)
        except (ClientError, BotoCoreError):
            return False
        return True

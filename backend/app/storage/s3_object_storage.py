"""``ObjectStorage`` on any S3 API (SeaweedFS locally), through ``aiobotocore``."""

from typing import TYPE_CHECKING

from botocore.exceptions import BotoCoreError, ClientError

if TYPE_CHECKING:
    from types_aiobotocore_s3 import S3Client

RETENTION_DAYS = 7
ALREADY_CREATED = frozenset({"BucketAlreadyOwnedByYou", "BucketAlreadyExists"})


class S3ObjectStorage:
    """One bucket, whole-object reads and writes, and a 7-day expiry rule (AD-012)."""

    def __init__(self, client: "S3Client", bucket: str) -> None:
        self._client = client
        self._bucket = bucket

    async def ensure_bucket(self) -> None:
        """Create the bucket and its lifecycle rule when missing.

        Every API process runs this at start, so on a fresh store two of them can race to
        create the bucket; the loser's "already exists" answer means the bucket is there.
        """
        try:
            await self._client.head_bucket(Bucket=self._bucket)
        except ClientError:
            await self._create_bucket()

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

    async def _create_bucket(self) -> None:
        try:
            await self._client.create_bucket(Bucket=self._bucket)
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") not in ALREADY_CREATED:
                raise

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

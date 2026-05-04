from __future__ import annotations

import asyncio
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from time import time
from uuid import uuid4

from app.core.config import settings


class StorageProviderError(RuntimeError):
    pass


class StorageProvider(ABC):
    @abstractmethod
    async def upload_file(
        self,
        *,
        data: bytes,
        filename: str,
        content_type: str,
        folder: str,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    async def get_signed_url(self, *, key: str, expires_in: int | None = None) -> str:
        raise NotImplementedError

    @abstractmethod
    async def delete_file(self, *, key: str) -> None:
        raise NotImplementedError


class LocalStorageProvider(StorageProvider):
    def __init__(self, root_path: str) -> None:
        self.root_path = Path(root_path)
        self.root_path.mkdir(parents=True, exist_ok=True)

    async def upload_file(
        self,
        *,
        data: bytes,
        filename: str,
        content_type: str,
        folder: str,
    ) -> str:
        suffix = Path(filename).suffix.lower()
        key = f"{folder.strip('/')}/{uuid4().hex}{suffix}"
        path = self.root_path / key
        path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(path.write_bytes, data)
        return key

    async def get_signed_url(self, *, key: str, expires_in: int | None = None) -> str:
        expires_at = int(time() + (expires_in or settings.signed_url_expire_seconds))
        return f"/internal/local-storage/{key}?signature=local-dev&expires={expires_at}"

    async def delete_file(self, *, key: str) -> None:
        path = self.root_path / key
        if path.exists():
            await asyncio.to_thread(path.unlink)
            empty_parents = [path.parent]
            for parent in empty_parents:
                if parent != self.root_path and parent.exists():
                    try:
                        await asyncio.to_thread(parent.rmdir)
                    except OSError:
                        pass


class S3StorageProvider(StorageProvider):
    def __init__(self) -> None:
        if not settings.storage_bucket:
            raise StorageProviderError("STORAGE_BUCKET is required for S3/R2 storage")
        try:
            import boto3
        except ImportError as exc:
            raise StorageProviderError("boto3 is required for S3/R2 storage") from exc

        self.bucket = settings.storage_bucket
        self.client = boto3.client(
            "s3",
            region_name=settings.storage_region,
            endpoint_url=settings.storage_endpoint_url,
            aws_access_key_id=settings.storage_access_key_id,
            aws_secret_access_key=settings.storage_secret_access_key,
        )

    async def upload_file(
        self,
        *,
        data: bytes,
        filename: str,
        content_type: str,
        folder: str,
    ) -> str:
        suffix = Path(filename).suffix.lower()
        key = f"{folder.strip('/')}/{uuid4().hex}{suffix}"

        def put_object() -> None:
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
                ACL="private",
            )

        await asyncio.to_thread(put_object)
        return key

    async def get_signed_url(self, *, key: str, expires_in: int | None = None) -> str:
        def make_url() -> str:
            return self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expires_in or settings.signed_url_expire_seconds,
            )

        return await asyncio.to_thread(make_url)

    async def delete_file(self, *, key: str) -> None:
        await asyncio.to_thread(
            self.client.delete_object,
            Bucket=self.bucket,
            Key=key,
        )


def get_storage_provider() -> StorageProvider:
    provider = settings.storage_provider.lower()
    if provider == "local":
        return LocalStorageProvider(settings.storage_local_path)
    if provider in {"s3", "r2"}:
        return S3StorageProvider()
    raise StorageProviderError(f"Unsupported storage provider: {settings.storage_provider}")

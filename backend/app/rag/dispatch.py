import asyncio
from typing import Protocol
from uuid import UUID

from celery import Celery  # type: ignore[import-untyped]
from kombu.exceptions import OperationalError  # type: ignore[import-untyped]

from app.rag.errors import IndexDispatchError

INDEX_TASK_NAME = "rag.process_memory_index_job"


class IndexDispatcher(Protocol):
    """Boundary for announcing a committed durable index job."""

    async def enqueue(self, job_id: UUID) -> None:
        """Announce a job ID without carrying canonical memory content."""


class CeleryIndexDispatcher:
    """Publish durable job identifiers to Celery over Redis."""

    def __init__(self, celery_app: Celery) -> None:
        self._celery_app = celery_app

    async def enqueue(self, job_id: UUID) -> None:
        try:
            await asyncio.to_thread(
                self._celery_app.send_task,
                INDEX_TASK_NAME,
                args=[str(job_id)],
            )
        except (OSError, TimeoutError, OperationalError) as error:
            raise IndexDispatchError("Memory index dispatch failed") from error

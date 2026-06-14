from celery import Celery  # type: ignore[import-untyped]

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "yggdrasil-rag",
    broker=settings.redis_url,
    include=["app.rag.tasks"],
)
celery_app.conf.update(
    accept_content=["json"],
    task_serializer="json",
    result_backend=None,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    worker_soft_shutdown_timeout=15,
    broker_connection_retry_on_startup=True,
    beat_schedule={
        "rag-worker-heartbeat": {
            "task": "rag.worker_heartbeat",
            "schedule": 15.0,
        },
        "rag-recover-index-jobs": {
            "task": "rag.recover_index_jobs",
            "schedule": 15.0,
        },
    },
)

from celery import Celery

from app.core.config import load_settings
from app.core.logging import configure_logging

settings = load_settings()
configure_logging(settings.log_level)

celery_app = Celery("workmate", broker=str(settings.redis_url))
celery_app.conf.update(
    task_acks_late=True,  # redeliver if a worker dies mid-task; tasks must be idempotent
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    worker_hijack_root_logger=False,
    timezone="UTC",
)


@celery_app.task(name="system.ping")  # type: ignore[untyped-decorator]
def ping() -> str:
    return "pong"

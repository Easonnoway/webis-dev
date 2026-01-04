import os
from celery import Celery

# Default Redis URL
REDIS_URL = os.environ.get("WEBIS_REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "webis",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["src.webis.core.worker"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

import os

from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "anonshare",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["tasks.ai_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

celery_app.conf.beat_schedule = {
    "retrain-anomaly-model-every-6-hours": {
        "task": "tasks.retrain_anomaly_model",
        "schedule": crontab(minute=0, hour="*/6"),
    },
}

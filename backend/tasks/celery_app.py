from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "job_matcher",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["tasks.ingest_jobs", "tasks.reembed_user"],
)

celery_app.conf.timezone = "UTC"
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]

celery_app.conf.beat_schedule = {
    "ingest-jobs-daily": {
        "task": "tasks.ingest_jobs.run_ingestion",
        "schedule": crontab(hour=2, minute=0),
    }
}

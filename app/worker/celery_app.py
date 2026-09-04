from celery import Celery
import os

broker_url = os.getenv(
    "CELERY_BROKER_URL",
    "redis://localhost:6379/0"
)

result_backend = os.getenv(
    "CELERY_RESULT_BACKEND",
    "redis://localhost:6379/1"
)


celery_app = Celery(
    "bag_counter",
    broker = broker_url,
    backend = result_backend,
    include = ["app.worker.tasks"],
)

celery_app.conf.update(
    task_track_started = True,
    result_expires = 3600
)


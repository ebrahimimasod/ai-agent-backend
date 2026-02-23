import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('rag_wp')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

from config.settings import settings

app.conf.update(
    broker_url=settings.CELERY_BROKER_URL,
    result_backend=settings.CELERY_RESULT_BACKEND,
    task_track_started=True,
    worker_prefetch_multiplier=1,
)

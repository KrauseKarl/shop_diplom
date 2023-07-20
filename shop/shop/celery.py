import os
from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shop.settings")

app = Celery("shop", broker="redis://redis:6379/0", backend="redis://redis:6379/1")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.broker_url = "redis://redis:6379/0"
app.autodiscover_tasks()

import os
from celery import Celery
from django.conf import settings
# os.environ.setdefault('FORKED_BY_MULTIPROCESSING', '1')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.settings')
#   celery -A shop.celery:app  worker --pool=solo --loglevel=DEBUG --port=9090
#   --pool=prefork --concurrency=4

app = Celery(
    'shop',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/1'
)
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.broker_url = 'redis://redis:6379/0'
app.autodiscover_tasks()

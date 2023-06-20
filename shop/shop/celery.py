import os
from celery import Celery

# os.environ.setdefault('FORKED_BY_MULTIPROCESSING', '1')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.settings')
# "celery -A shop worker ol"

app = Celery('shop', broker="redis://localhost:6379", backend="redis://localhost:6379")
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
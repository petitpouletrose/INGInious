import inginious.backend.celeryconfig
from celery import Celery


app = Celery('celery_backend')
app.config_from_object('celeryconfig')
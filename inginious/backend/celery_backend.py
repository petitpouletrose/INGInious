from celery import Celery


app = Celery('celery_backend')
app.config_from_object('celeryconfig')

@app.task
def add(x, y):
    return x + y
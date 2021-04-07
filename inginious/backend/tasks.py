from inginious.backend.celery_backend import app

@app.task
def add(x, y):
    return x + y
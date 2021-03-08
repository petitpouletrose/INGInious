from celery import Celery

app = Celery('tasks', broker='tcp://*:4161')

@app.task
def add(x, y):
    return x + y

add(1,2)
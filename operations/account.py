from externals import ext_celery
from celery import shared_task
# TODO

@shared_task
def divide(x, y):
    import time
    time.sleep(5)
    return x / y
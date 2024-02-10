# celery_worker.py
from celery import Celery

celery_app = Celery('celery_worker', 
                    broker='redis://redis:6379/0',
                    result_backend = 'redis://redis:6379/0',
                    include=['tasks.celery_back_tasks'])



#'redis://redis:6379/0'#
#redis://localhost:6379/0
# celery_worker.py
from celery import Celery

# celery_app = Celery('celery_worker', 
#                     broker='redis://redis:6379/0',
#                     result_backend = 'redis://redis:6379/0',
#                     include=['tasks.celery_back_tasks'])

celery_app = Celery('celery_worker', 
                    broker='amqp://guest:guest@rabbitmq:5672//',
                    result_backend='redis://redis:6379/0',
                    include=['tasks.celery_back_tasks','tasks.celery_back_tasks_image'])
celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    #worker_state_db="./celery-state.db",
)


#'redis://redis:6379/0'#
#redis://localhost:6379/0
from celery_worker import celery_app

@celery_app.task(name='create_task')
def create_task(data):
    # Placeholder for task logic
    print(f"Processing data: {data}")
    # Imagine some long-running process here
    return {"processed_data": data}
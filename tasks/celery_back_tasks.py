from celery import chain, chord
from celery_worker import celery_app
from tasks.celery_helper import initial_task,process_item, filter_results, classify_urls,combine_results,execute_and_return_chord_result

@celery_app.task(name='create_task')
def create_task(data):
    brand = data[0]
    sku = data[1]
    task_id = execute_workflow(brand,sku)
    print(task_id)
    if task_id: 
        return task_id
    else:
        task_id = 'Brand Missing'
        return task_id


def execute_workflow(brand, sku):
    sku_variations = initial_task(brand, sku)
    if sku_variations:
        workflow = chain(
            chord(
                (process_item.s(item) for item in sku_variations),
                combine_results.s()  # Callback receives results with items
            ),
            filter_results.s(brand),
            classify_urls.s(), 
            execute_and_return_chord_result.s(brand)
        )
        
        result = workflow.apply_async()
        return result
    else:
        return None
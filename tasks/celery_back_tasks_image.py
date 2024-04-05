from celery import chain, chord
from celery_worker import celery_app
from tasks.celery_helper_image import initial_task,process_item, filter_results, classify_urls,combine_results,choose_result,process_itemV2

@celery_app.task(name='create_task_image')
def create_task_image(data):
    brand = data[0]
    sku = data[1]
    task_id = execute_workflow(brand,sku)
    return task_id


def execute_workflow(brand, sku):
    sku_variations = initial_task(brand, sku)
    if sku_variations:
        workflow = chain(
            chord(
                (process_itemV2.s(item,brand) for item in sku_variations),
                combine_results.s()  # Callback receives results with items
            ),
            filter_results.s(brand,sku),
            #classify_urls.s(),
            #choose_result.s(sku)
        )
        
        result = workflow.apply_async()
        return result
    else:
        return None
from celery import chain, chord
from celery_worker import celery_app
from tasks.celery_image_tasks import initial_task, process_itemV2, combine_results,filter_results

@celery_app.task(name='create_task_image')
def create_task_image(data):
    print(data)
    brand = data[0]
    sku = data[1]
    entry_id = data[2]
    file_id = data[3]
    task_id= execute_workflow(brand, sku, entry_id, file_id)
    return task_id




def execute_workflow(brand, sku, entry_id, file_id):

    sku_variations = initial_task(brand, sku)

    if sku_variations:
        workflow = chain(
            chord(
                (process_itemV2.s(item, brand) for item in sku_variations),
                combine_results.s()  # Callback receives results with items
            ),
            filter_results.s(brand, sku, entry_id, file_id),
            # classify_urls.s(),
            # choose_result.s(sku)
        )

        result = workflow.apply_async()
        return result
    else:
        return None
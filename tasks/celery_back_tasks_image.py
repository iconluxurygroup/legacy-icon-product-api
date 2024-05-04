from celery import chain, chord,group
from celery_worker import celery_app
from tasks.celery_image_tasks import initial_task, process_itemV2, combine_results,filter_results,process_item_cms

@celery_app.task(name='create_task_image')
def create_task_image(data):
    print(data)
    brand = data[0]
    sku = data[1]
    entry_id = data[2]
    file_id = data[3]
    task_id= execute_workflow(brand, sku, entry_id, file_id)
    return task_id


@celery_app.task(name='create_task_image_cms')
def create_task_image_cms(data):
    print(data)
    brand = data[0]
    sku = data[1]
    entry_id = data[2]
    file_id = data[3]
    task_id= execute_workflow_cms(brand, sku, entry_id, file_id)
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

def execute_workflow_cms(brand, sku, entry_id, file_id):
        sku_variations = initial_task(brand, sku)

        if sku_variations:
            flow = group([process_item_cms.s(item, brand,entry_id, file_id) for item in sku_variations])
            result = flow.apply_async()
            return result
        else:
            return None



# job = group([
#             add.s(2, 2),
#             add.s(4, 4),
#             add.s(8, 8),
#             add.s(16, 16),
#             add.s(32, 32),
# ])
#
# result = job.apply_async()
#
# result.ready()  # have all subtasks completed?
# True
# result.successful() # were all subtasks successful?
# True
# result.get()
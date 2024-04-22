from celery import chain, chord
from celery_worker import celery_app
from tasks.celery_image_tasks import (initial_task, process_itemV2, combine_results)
#,filter_results

@celery_app.task(name='create_task_image')
def create_task_image(data):
    print(data)
    brand = data[0]
    sku = data[1]
    entry_id = data[2]
    file_id = data[3]
    task_id= execute_workflow(brand, sku, entry_id, file_id)
    return task_id




# def execute_workflow(brand, sku, entry_id, file_id):
#
#     #sku_variations = initial_task(brand, sku)
#
#     #if sku_variations:
#     workflow = chain(
#         process_itemV2.s(item, brand) for item in sku,
#                      filter_results.s(brand, sku, entry_id, file_id), )
#             #chord(
#             #process_itemV2.s(item, brand) for item in [sku],
#                 #combine_results.s()  # Callback receives results with items
#             #),
#
#             # classify_urls.s(),
#             # choose_result.s(sku)
#       #  )
#
#     result = workflow.apply_async()
#     return result


def execute_workflow(brand, sku, entry_id, file_id):
    # Create a list of tasks for each item in sku to process
    process_tasks = process_itemV2.s(sku, brand,entry_id,file_id)

    # Chain all process tasks with the filter_results task at the end

    #process_tasks = process_tasks[0]
    # Apply the workflow asynchronously and return the result
    result = process_tasks.apply_async()
    return result
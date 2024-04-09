from celery import chain, chord
from celery_worker import celery_app
from tasks.celery_helper_image import initial_task,process_item, filter_results, classify_urls,combine_results,choose_result,process_itemV2
from settings import HOST_V,DB_V,USER_V,PASS_V,PORT_V
import mysql.connector.pooling

@celery_app.task(name='create_task_image')
def create_task_image(data):
    print(data)
    brand = data[0]
    sku = data[1]
    entry_id = data[2]
    file_id = data[3]
    task_id, connection_pool = execute_workflow(brand, sku, entry_id, file_id)
    return task_id




def execute_workflow(brand, sku, entry_id, file_id):
    conn_params = {
        'host': HOST_V,
        'database': DB_V,
        'user': USER_V,
        'passwd': PASS_V,
        'port': PORT_V,
    }

    # Create a connection pool
    connection_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="mypool",
        pool_size=2,
        **conn_params
    )

    sku_variations = initial_task(brand, sku)

    if sku_variations:
        workflow = chain(
            chord(
                (process_itemV2.s(item, brand,connection_pool) for item in sku_variations),
                combine_results.s()  # Callback receives results with items
            ),
            filter_results.s(brand, sku, entry_id, file_id, connection_pool),
            # classify_urls.s(),
            # choose_result.s(sku)
        )

        result = workflow.apply_async()
        return result, connection_pool
    else:
        return None, connection_pool
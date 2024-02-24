import json
from typing import Dict
from celery import chord,shared_task
from celery.result import AsyncResult
from celery_worker import celery_app
from tasks.classes_and_utility import BrandSettings,SKUManager,SearchEngine,FilterUrls,DataFetcher
from settings import BRANDSETTINGSPATH


def fetch_task_result(task_id: str) -> dict:
    """
    Fetches the result of a Celery task by its ID. If the task is part of a workflow with subtasks,
    it recursively fetches the results of all subtasks.

    :param task_id: The ID of the Celery task.
    :return: A dictionary with the task status and result.
    """
    if task_id is None:
        return {'status': 'Invalid', 'result': None}
    task_result = AsyncResult(task_id, app=celery_app)
    if not task_result.ready():
        # The task is still processing
        return {'status': 'Processing', 'result': None}
    #@!!!!!!
    if task_result:
        result = task_result.get()
    else:
        return {'status': 'Invalid', 'result': None}   
    if isinstance(result, list):
        # The result is a list, potentially indicating a workflow with subtasks
        final_results = []
        for item in result:
            if isinstance(item, list) and item:
                subtask_id = item[0]
                if subtask_id is not None:
                    subtask_result = fetch_task_result(subtask_id)
                    final_results.append(subtask_result)
                else:
                    final_results.append(item)
        return {'status': 'Completed', 'result': final_results}
    ##!!! CATCH RESULT BY DICT
    elif isinstance(result, dict):
        return {'status': 'Completed', 'result': result}
    else:
        # The task is completed and there are no further nested tasks
        ####TRY FAILS RESULT = NONE
       # return {'status': 'Completed', 'result': result}
        return {'status': 'Invalid', 'result': result}

def filter_price(result):
    if result and isinstance(result, dict) and 'details' in result and result['details']:
        if 'prices' in result['details'] and result['details']['prices']:
            return True # Return immediately if criteria are met
    elif result and isinstance(result, list):
        for detail in result:
            if detail and 'details' in detail and detail['details'] and 'prices' in detail['details'] and detail['details']['prices']:
                return True # Return immediately if any detail in list meets criteria
def choose_best_result(results):
    for result in results:
        if filter_price(result):
            return result
        return None # Ensure there's a fallback return

@shared_task
def initial_task(brand, sku):
    # Logic to generate a list based on brand and sku
    brand_settings = BrandSettings(json.loads(open(BRANDSETTINGSPATH,encoding='utf-8').read()))

    out = SKUManager(brand_settings, sku, brand).variations
    if out:
        print(out,"------------------------------------------")
        print("Sku Variation Len: ",len(out))
        return out
    else:
        return None

@shared_task
def process_group_results(results):
    # Process results from group, potentially just aggregating them
    #!aggregated_results = [result for result in results] # Simplified example
    aggregated_results = [result for result in (results or [])]

    #return choose_best_result(aggregated_results)
    return {"task_name": "process_group_results", "result": choose_best_result(aggregated_results) }
@shared_task(bind=True)
def create_chord(self,data, brand,):
    # Setup the tasks to be executed in parallel within the group
    tasks_group = [fetch_and_parse_html.s(url_info, brand) for url_info in data]
    # Specify the callback task to process results after the group has finished
    # Note: The callback task should be defined to accept the results from the group.
    callback_task = process_group_results.s()
    # Return the chord signature without immediately invoking it
    # This allows Celery to properly integrate and execute it within the workflow
    return chord(tasks_group, callback_task).apply_async()

@shared_task
def process_item(item):#get html and return list of parsed google urls
    urls = SearchEngine(item).parsed_results
    return (urls, item)

@shared_task
def filter_results(url_list_with_items, brand):
    if url_list_with_items is None:
        url_list_with_items = []
    filtered_url_list_with_info = []

    # Create a mapping from URL to its corresponding dictionary
    url_to_original_dict = {url_dict['url']: url_dict for url_dict in url_list_with_items}
    
    # Extract URLs and apply filtering
    urls = [url_dict['url'] for url_dict in url_list_with_items]
    
    filtered_urls = FilterUrls(urls, brand).filtered_urls

    print(filtered_urls,"------------------------------------------")
    # Ensure filtered_urls is iterable
    if not filtered_urls:
        filtered_urls = []
        return None
    if filtered_urls:    
        # Include only the filtered URLs, their corresponding original dictionary, and type
        for filtered_url_info in filtered_urls:
            print(filtered_url_info, "------------------------------------------")
            filtered_url = filtered_url_info[0] # Assuming the URL is the first element in the list
            url_type = filtered_url_info[1] # Extract type from the second element in the list
            if filtered_url in url_to_original_dict:
                original_dict = url_to_original_dict[filtered_url]
                # Update the original dictionary with the type
                original_dict.update({'type': url_type})
                filtered_url_list_with_info.append(original_dict)

                return filtered_url_list_with_info
    

@shared_task
def combine_results(results_with_items):
    aggregate_result = []
    for urls, item in results_with_items:
        # Assuming urls is a list of strings
        for url in urls:
            # Combine url with item, for example, by creating a dictionary
            modified_url = {'url': url, 'item': item}
            aggregate_result.append(modified_url)
            return aggregate_result

@shared_task
def fetch_and_parse_html(classified_url: Dict[str, str],brand_name: str):
    # Placeholder logic to fetch and parse HTML for a single URL
    parsed_data = DataFetcher(classified_url,brand_name).parsed_products
    l_product_detail = {'url': classified_url['url'],'type' : classified_url['type'],'brand':brand_name,'variation':classified_url['variation'], 'details': parsed_data}
    return l_product_detail
@shared_task
def classify_urls(url_list):
    classified_urls = []
    if not url_list:
        return None
    for url_dict in url_list:
        url = url_dict['url']
        url_type = url_dict['type']
        variation = url_dict['item']
        classified_urls.append({'url': url, 'type': url_type, 'variation': variation})
        return classified_urls


@shared_task(bind=True)
def execute_and_return_chord_result(self, data, brand):
    if not data:
       data = []
        
    # Setup the tasks to be executed in parallel within the group
    tasks_group = [fetch_and_parse_html.s(url_info, brand) for url_info in data]
    # Specify the callback task to process results after the group has finished
    callback_task = process_group_results.s()
    # Create the chord and execute it
    chord_result = chord(tasks_group, callback_task).apply_async()
    # Wait for the chord's result and return it
    return chord_result


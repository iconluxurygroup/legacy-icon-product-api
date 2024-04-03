import json
from typing import Dict
from celery import chord,shared_task
from celery.result import AsyncResult
from celery_worker import celery_app
from tasks.image_utility import SKUManager,SearchEngine,FilterUrls,SearchEngineV2
from tasks.classes_and_utility import BrandSettings
from settings import BRANDSETTINGSPATH

def fetch_task_result_image(task_id: str) -> dict:
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
                    subtask_result = fetch_task_result_image(subtask_id)
                    final_results.append(subtask_result)
                else:
                    final_results.append(item)
        return {'status': 'Completed', 'result': final_results}
    else:
        # The task is completed and there are no further nested tasks
        return {'status': 'Completed', 'result': result}

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
    # Logic to generate a list based on brand and sk
    out = SKUManager(sku, brand).variations
    print(out,"------------------------------------------")
    if out:
        print("Sku Variation Len: ",len(out))
        return out
@shared_task
def process_group_results(results):
    # Process results from group, potentially just aggregating them
    #!aggregated_results = [result for result in results] # Simplified example
    aggregated_results = [result for result in (results or [])]

    #return choose_best_result(aggregated_results)
    return {"task_name": "process_group_results", "result": choose_best_result(aggregated_results) }
# @shared_task(bind=True)
# def create_chord(self,data, brand,):
#     # Setup the tasks to be executed in parallel within the group
#     tasks_group = [fetch_and_parse_html.s(url_info, brand) for url_info in data]
#     # Specify the callback task to process results after the group has finished
#     # Note: The callback task should be defined to accept the results from the group.
#     callback_task = process_group_results.s()
#     # Return the chord signature without immediately invoking it
#     # This allows Celery to properly integrate and execute it within the workflow
#     return chord(tasks_group, callback_task).apply_async()
def get_brand_domains(brand):
    brand_settings = BrandSettings(json.loads(open(BRANDSETTINGSPATH,encoding='utf-8').read())).get_brand_img_domains(brand)
    return brand_settings
 
    
@shared_task
### IF ZIP OR SEARCH IS LESS THAN MIGHT CAUSE ISSUES
def process_item(item,brand):#get html and return list of parsed google urls
    processed_items = []
    search_engine = SearchEngineV2()
    results = search_engine.get_results(item)
    if results:
    #urls = search_engine.urls_list
    #descriptions = search_engine.descriptions_list
        urls = results[0]
        descriptions = results[1]
        #        
        # Check if either urls or descriptions list is empty
        if not urls or not descriptions:
            raise ValueError("Either 'urls' or 'descriptions' list is empty.")

        # Check if urls and descriptions lists are of unequal lengths
        if len(urls) != len(descriptions):
            
            raise ValueError(f"'urls'{len(urls)} and 'descriptions' {len(descriptions)}lists are of unequal lengths.\n{urls}-----\n{descriptions}")
        for url, description in zip(urls, descriptions):
            processed_items.append({
                    'url': url,
                    'description': description,
                    'sku': item,
                    'brand': brand,
                    'brand_domains':get_brand_domains(brand)
                })
        return processed_items
    else:
        return process_item(item,brand)


@shared_task
def filter_results(url_list_with_items, brand, sku):
    if not url_list_with_items:
        return []# Return immediately if no URLs are provided????????????????????????______________________________

    filter_urls_instance = FilterUrls(url_list_with_items, brand, sku)
    filter_results = filter_urls_instance.filtered_result
    if (type(filter_results) == list) and (len(filter_results) > 1):
        return filter_results[0]
    else:
        return filter_results
# @shared_task
# def combine_results(results_with_items):
#     print(results_with_items)
#     aggregate_result = []
#     for urls, item in results_with_items:
#         # Assuming urls is a list of strings
#         for url in urls:
#             # Combine url with item, for example, by creating a dictionary
#             modified_url = {'url': url, 'item': item}
#             aggregate_result.append(modified_url)
#             return aggregate_result
@shared_task
def combine_results(results_with_items):
    aggregate_result = []
    for result_list in results_with_items:
        # Assuming result_list is a list of dictionaries
        aggregate_result.extend(result_list)
    return aggregate_result
# @shared_task
# def fetch_and_parse_html(classified_url: Dict[str, str],brand_name: str):
#     # Placeholder logic to fetch and parse HTML for a single URL
#     parsed_data = DataFetcher(classified_url,brand_name).parsed_products
#     l_product_detail = {'url': classified_url['url'],'type' : classified_url['type'],'brand':brand_name,'variation':classified_url['variation'], 'details': parsed_data}
#     return l_product_detail

from collections import Counter

from collections import Counter

def normalize(s):
    """Normalize a SKU string."""
    if not isinstance(s, str):
        raise ValueError(f"Expected a string for normalization, received {type(s)}: {s}")
    return ''.join(s.split()).lower()

############################################################################################################
#CHOOSE RESULT FIRST CHECKING
@shared_task
def choose_result(classified_urls, sku):
    # Debug: Log the types of received arguments
    print(f"Debug: classified_urls type: {type(classified_urls)}, sku type: {type(sku)}")
    print(f"Debug: SKU: {sku}")

    # Proceed with your existing logic
    try:
        sku_norm = normalize(sku)
    except ValueError as e:
        # Log detailed error information to help with debugging
        print(f"Error normalizing SKU: {e}")
        return

    # Rest of the task logic...

    sku_norm = normalize(sku)

    # Initialize tiers
    tier1, tier2, tier3 = [], [], []

    # Prepare a counter for the normalized SKU for comparison
    sku_counter = Counter(sku_norm)
    if classified_urls:
        for url_dict in classified_urls:
            variation = url_dict.get('item', '')
            if isinstance(variation, str):
                variation_norm = normalize(variation)

                # Exact match
                if variation_norm == sku_norm:
                    tier1.append(url_dict)
                # All characters match but format different
                elif Counter(variation_norm) == sku_counter:
                    tier2.append(url_dict)
                # Some characters missing
                else:
                    tier3.append(url_dict)

        # Choose logic (simplified for demonstration)
        chosen_url = None
        if tier1:
            chosen_url = tier1[0]
        elif tier2:
            chosen_url = tier2[0]
        elif tier3:
            chosen_url = tier3[0]
        
        return chosen_url
    else:
        print('No classified URLs found')
        return ['None found']



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


# @shared_task(bind=True)
# def execute_and_return_chord_result(self, data, brand):
#     data = data or []
#     # Setup the tasks to be executed in parallel within the group
#     tasks_group = [fetch_and_parse_html.s(url_info, brand) for url_info in data]
#     # Specify the callback task to process results after the group has finished
#     callback_task = process_group_results.s()
#     # Create the chord and execute it
#     chord_result = chord(tasks_group, callback_task).apply_async()
#     # Wait for the chord's result and return it
#     return chord_result


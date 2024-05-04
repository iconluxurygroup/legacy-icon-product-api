# tasks/celery_tasks.py
import requests, base64, zlib
from celery import shared_task
from tasks.image_utility import SKUManager
from tasks.FilterImageV2 import FilterUrlsV2
from tasks.google_parser import get_original_images as GP
from settings import HOST_V,DB_V,USER_V,PASS_V,PORT_V
import mysql.connector.pooling

global_connection_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=32,
    host=HOST_V,
    database=DB_V,
    user=USER_V,
    password=PASS_V,
    port=PORT_V
)
@shared_task
def initial_task(brand, sku):
    # Logic to generate a list based on brand and sk
    out = SKUManager(sku, brand).variations
    print(out,"------------------------------------------")
    if out:
        print("Sku Variation Len: ",len(out))
        return out
@shared_task
def combine_results(results_with_items):
    aggregate_result = []
    for result_list in results_with_items:
        # Assuming result_list is a list of dictionaries
        aggregate_result.extend(result_list)
    return aggregate_result

@shared_task
def process_itemV2(item, brand):  # get html and return list of parsed google urls
    processed_items = []
    search_engine = SearchEngineV3()
    search_engine.get_results(item)

    if search_engine.image_url_list and search_engine.image_desc_list and search_engine.image_source_list:
        image_url_list = search_engine.image_url_list
        image_desc_list = search_engine.image_desc_list
        image_source_list = search_engine.image_source_list

        # Check if either urls or descriptions list is empty
        if not image_url_list or not image_desc_list or not image_source_list:
            raise ValueError("Either 'urls' or 'descriptions' list is empty. or source is empty")

        # Check if urls and descriptions lists are of unequal lengths
        if len(image_url_list) != len(image_desc_list):
            # Determine the minimum length
            min_length = min(len(image_url_list), len(image_desc_list))

            # Truncate the lists to the minimum length
            image_url_list = image_url_list[:min_length]
            image_desc_list = image_desc_list[:min_length]

        for url, description in zip(image_url_list, image_desc_list):
            processed_items.append({
                'url': url,
                'description': description,
                'sku': item,
                'brand': brand,
                'brand_domains': [] #get_brand_domains(brand)
            })
        return processed_items
    else:
        print('endless lop')
        return process_itemV2(item, brand)

@shared_task
def process_item_cms(item, brand, entry_id, file_id):  # get html and return list of parsed google urls
        processed_items = []
        search_engine = SearchEngineV3()
        search_engine.get_results(item)

        if search_engine.image_url_list and search_engine.image_desc_list and search_engine.image_source_list:
            image_url_list = search_engine.image_url_list
            image_desc_list = search_engine.image_desc_list
            image_source_list = search_engine.image_source_list

            # Check if either urls or descriptions list is empty
            if not image_url_list or not image_desc_list or not image_source_list:
                raise ValueError("Either 'urls' or 'descriptions' list is empty. or source is empty")

            # Check if urls and descriptions lists are of unequal lengths
            if len(image_url_list) != len(image_desc_list):
                # Determine the minimum length
                min_length = min(len(image_url_list), len(image_desc_list))

                # Truncate the lists to the minimum length
                image_url_list = image_url_list[:min_length]
                image_desc_list = image_desc_list[:min_length]

            for url, description in zip(image_url_list, image_desc_list):
                processed_items.append({
                    'url': url,
                    'description': description,
                    'sku': item,
                    'brand': brand,
                    'brand_domains': []  # get_brand_domains(brand)
                })
            write_results_to_mysql(image_url_list, int(entry_id), file_id)
            return processed_items
        else:
            print('endless lop')
            return process_item_cms(item, brand, entry_id, file_id)
@shared_task
def filter_results(url_list_with_items, brand, sku, entry_id, file_id):
    print(entry_id,file_id)
    if not url_list_with_items:
        return []# Return immediately if no URLs are provided????????????????????????______________________________

    filter_urls_instance = FilterUrlsV2(url_list_with_items, brand, sku)
    filter_results = filter_urls_instance.filtered_result
    if not filter_results:
        print('no result returned from filterImage')
        return []
    if (type(filter_results) == list) and (len(filter_results) > 1):
        print('im in!')
        write_results_to_mysql(filter_results[0], entry_id, file_id)
        return filter_results[0]
    else:
        write_results_to_mysql(filter_results, entry_id, file_id)
        return filter_results
# def write_results_to_mysql(result, entry_id, file_id):
#     global global_connection_pool
#     print(result)
#     print('Writing to db')
#     image_url = 'None found in this filter'
#     if result != 'None found in this filter' and result is not None:
#         image_url = result
#
#     query = "UPDATE utb_ImageScraperResult SET ImageURL = %s,CompleteTime = CURRENT_TIMESTAMP WHERE EntryID = %s AND FileID = %s"
#     query_params = (image_url, entry_id, file_id)
#
#     connection = global_connection_pool.get_connection()
#     cursor = connection.cursor()
#
#     cursor.execute(query, query_params)
#     connection.commit()
#
#     cursor.close()
#     connection.close()
#
#     print(f"Data written to DB for EntryID: {entry_id} and FileID: {file_id}")
def write_results_to_mysql(image_url_list, entry_id, file_id):
    """
    Inserts multiple image URLs into the database with the current timestamp for the specified entry_id and file_id.

    Parameters:
    image_url_list (list of str): List of image URLs.
    entry_id (int): The identifier for the entry.
    file_id (int): The identifier for the file.

    """
    import logging

    global global_connection_pool
    logging.info("Received image URL list: %s", image_url_list)
    logging.info('Starting batch insert into db')

    query = """
    INSERT INTO utb_ImageScraperResult (ImageURL, EntryID, FileID, CompleteTime)
    VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
    """

    try:
        with global_connection_pool.get_connection() as connection:
            with connection.cursor() as cursor:
                for image_url in image_url_list:
                    if image_url:  # Ensure non-empty URLs are processed
                        print(image_url)
                        
                        query_params = (image_url, entry_id, file_id)
                        cursor.execute(query, query_params)
                connection.commit()
                logging.info(f"Batch data inserted into DB for EntryID: {entry_id} and FileID: {file_id}")
    except Exception as e:
        logging.error("Failed to insert into DB: %s", e)
        connection.rollback()
        # Optionally, handle or re-raise exception for further processing

class SearchEngineV3:
    def __init__(self):
        global global_connection_pool
        self.image_url_list = None
        self.image_desc_list = None
        self.image_source_list = None
        self.conn_params = {
            'host': HOST_V,
            'database': DB_V,
            'user': USER_V,
            'passwd': PASS_V,
            'port': PORT_V,
        }
        self.connection_pool = global_connection_pool
        self.endpoint = self.get_endpoint_mysql()


    def get_results(self, variation):
        workflow_results = self.search_row(variation, self.endpoint)
        print(type(workflow_results))
        if workflow_results:
            self.image_url_list = workflow_results[0]
            self.image_desc_list = workflow_results[1]
            self.image_source_list = workflow_results[2]
        else:
            return None

    def search_row(self,search_string, endpoint):
        search_url = f"{endpoint}?query={search_string}"
        print(search_url)
        try:
            response = requests.get(search_url, timeout=60)
            print(response.status_code)
            if response.status_code != 200 or response.json().get('body') is None:
                print('trying again 1')
                self.remove_endpoint_mysql(endpoint)
                n_endpoint = self.get_endpoint_mysql()
                return self.search_row(search_string, n_endpoint)  # Add return here
            else:
                response_json = response.json()
                result = response_json.get('body', None)
                if result:
                    unpacked_html = self.unpack_content(result)
                    parsed_data = GP(unpacked_html)
                    if parsed_data is None:
                        print('trying again 2')
                        self.remove_endpoint_mysql(endpoint)
                        n_endpoint = self.get_endpoint_mysql()
                        return self.search_row(search_string, n_endpoint)  # Add return here
                    if parsed_data[0]:
                        print('data found')
                        if parsed_data[0][0] == 'No start_tag or end_tag':
                            print('trying again 3')
                            self.remove_endpoint_mysql(endpoint)
                            n_endpoint = self.get_endpoint_mysql()
                            return self.search_row(search_string, n_endpoint)
                        else:
                            print('parsed data!')
                            image_url = parsed_data[0]
                            image_desc = parsed_data[1]
                            image_source = parsed_data[2]

                            print(
                                f'Image URL: {type(image_url)} {image_url}\nImage Desc:  {type(image_desc)} {image_desc}\nImage Source:{type(image_source)}  {image_source}')
                            if image_url and image_desc and image_source:
                                return image_url, image_desc, image_source
                            else:
                                #### only for todd snyder fix
                                if image_url[0]:
                                    return [image_url[0]], ['NO DESCRIPTION'], ['NO SOURCE']
                                print('trying again 4')
                                self.remove_endpoint_mysql(endpoint)
                                n_endpoint = self.get_endpoint_mysql()
                                return self.search_row(search_string, n_endpoint)
                    else:
                        print('trying again no data')
                        self.remove_endpoint_mysql(endpoint)
                        n_endpoint = self.get_endpoint_mysql()
                        return self.search_row(search_string, n_endpoint)

        except requests.RequestException as e:
            print('trying again 5')
            self.remove_endpoint_mysql(endpoint)
            n_endpoint = self.get_endpoint_mysql()
            print(f"Error making request: {e}\nTrying Again: {n_endpoint}")
            return self.search_row(search_string, n_endpoint)

    # def get_endpoint_mysql(self):
    #     connection = mysql.connector.connect(**self.conn_params)
    #     cursor = connection.cursor()
    #
    #     # Adjusted SQL query for MySQL. Note: The ORDER BY RAND() is less performant on large datasets.
    #     sql_query = "SELECT EndpointURL FROM utb_Endpoints WHERE EndpointIsBlocked = 0 ORDER BY RAND() LIMIT 1"
    #
    #     cursor.execute(sql_query)
    #     endpoint_url = cursor.fetchone()
    #
    #     # No need to commit after a SELECT statement, so it's removed.
    #     cursor.close()
    #     connection.close()
    #
    #     if endpoint_url:
    #         (endpoint,) = endpoint_url
    #         print(endpoint)
    #     else:
    #         print("No EndpointURL")
    #         endpoint = "No EndpointURL"
    #
    #     return endpoint
    def get_endpoint_mysql(self):
        connection = self.connection_pool.get_connection()
        cursor = connection.cursor()

        sql_query = "SELECT EndpointURL FROM utb_Endpoints WHERE EndpointIsBlocked = 0 ORDER BY RAND() LIMIT 1"

        cursor.execute(sql_query)
        endpoint_url = cursor.fetchone()

        cursor.close()
        connection.close()

        if endpoint_url:
            (endpoint,) = endpoint_url
            print(endpoint)
        else:
            print("No EndpointURL")
            endpoint = "No EndpointURL"

        return endpoint
    # def remove_endpoint_mysql(self,endpoint):
    #     # conn_params is a dictionary containing MySQL connection parameters such as
    #     # host, database, user, and password.
    #     connection = mysql.connector.connect(**self.conn_params)
    #     cursor = connection.cursor()
    #     # Using parameterized queries to prevent SQL injection
    #     sql_query = "UPDATE utb_Endpoints SET EndpointIsBlocked = 1 WHERE EndpointURL = %s"
    #     cursor.execute(sql_query, (endpoint,))
    #     connection.commit()
    #     cursor.close()
    #     connection.close()

    def remove_endpoint_mysql(self, endpoint):
        connection = self.connection_pool.get_connection()
        cursor = connection.cursor()

        sql_query = "UPDATE utb_Endpoints SET EndpointIsBlocked = 1 WHERE EndpointURL = %s"
        cursor.execute(sql_query, (endpoint,))
        connection.commit()

        cursor.close()
        connection.close()

    def unpack_content(self,encoded_content):
        if encoded_content:
            compressed_content = base64.b64decode(encoded_content)
            original_content = zlib.decompress(compressed_content)
            # with open('text.html', 'w') as file:
            #     file.write(str(original_content))
            return original_content  # Return as binary data
        return None
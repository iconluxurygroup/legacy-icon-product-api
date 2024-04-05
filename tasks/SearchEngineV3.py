import mysql.connector
import unicodedata,requests, random, time, base64, zlib
from tasks.google_parser import get_original_images as GP
from settings import HOST_V,DB_V,USER_V,PASS_V,PORT_V

class SearchEngineV3:
    def __init__(self):
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
                            print('trying again 4')
                            self.remove_endpoint_mysql(endpoint)
                            n_endpoint = self.get_endpoint_mysql()
                            return self.search_row(search_string, n_endpoint)
        except requests.RequestException as e:
            print('trying again 5')
            self.remove_endpoint_mysql(endpoint)
            n_endpoint = self.get_endpoint_mysql()
            print(f"Error making request: {e}\nTrying Again: {n_endpoint}")
            return self.search_row(search_string, n_endpoint)

    def get_endpoint_mysql(self):
        connection = mysql.connector.connect(**self.conn_params)
        cursor = connection.cursor()

        # Adjusted SQL query for MySQL. Note: The ORDER BY RAND() is less performant on large datasets.
        sql_query = "SELECT EndpointURL FROM utb_Endpoints WHERE EndpointIsBlocked = 0 ORDER BY RAND() LIMIT 1"

        cursor.execute(sql_query)
        endpoint_url = cursor.fetchone()

        # No need to commit after a SELECT statement, so it's removed.
        cursor.close()
        connection.close()

        if endpoint_url:
            (endpoint,) = endpoint_url
            print(endpoint)
        else:
            print("No EndpointURL")
            endpoint = "No EndpointURL"

        return endpoint

    def remove_endpoint_mysql(self,endpoint):
        # conn_params is a dictionary containing MySQL connection parameters such as
        # host, database, user, and password.
        connection = mysql.connector.connect(**self.conn_params)
        cursor = connection.cursor()
        # Using parameterized queries to prevent SQL injection
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
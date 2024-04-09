import json,re,requests,logging,base64,random,time
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from tasks.LR import LR
import zlib
from tasks.classes_and_utility import BrandSettings
from settings import BRANDSETTINGSPATH,SERVERLESS_URL_SETTINGS
from html.parser import HTMLParser
import html
import string
import unicodedata
from tasks.google_parser import get_original_images as GP
import mysql.connector
# Enhanced HTML Parser for extracting specific image data
class EnhancedHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []
        self.current_item = {}
        self.collecting_data = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == 'td' and 'align' in attrs_dict and attrs_dict['align'] == 'center':
            self.collecting_data = True
            self.current_item = {'thumbnail_url': '', 'description': '', 'website': ''}
        elif tag == 'img' and self.collecting_data:
            self.current_item['thumbnail_url'] = attrs_dict.get('src', '')
        elif tag == 'a' and self.collecting_data:
            self.current_item['website'] = attrs_dict.get('href', '').split('?q=')[1].split('&')[0] if '?q=' in attrs_dict.get('href', '') else ''

    def handle_data(self, data):
        if self.collecting_data:
            if 'description' not in self.current_item or not self.current_item['description']:
                self.current_item['description'] = data

    def handle_endtag(self, tag):
        if tag == 'td' and self.collecting_data:
            self.items.append(self.current_item)
            self.collecting_data = False
            self.current_item = {}

    def error(self, message):
        print(f"An error occurred: {message}")


class SKUManager:
    def __init__(self,sku, brand=None):
        self.variations=self.generate_variations(sku, brand)
    
    def generate_variations(self, input_sku,brand_name ):
        if brand_name:
            #brand_variations = self.handle_brand_sku(input_sku, brand_rule)
            blind_variations = self.handle_sku(input_sku,brand_name)
            #return brand_variations + blind_variations# + [input_sku]
            return blind_variations
        else:
            blind_variations = self.handle_sku(input_sku,brand_name)
            return blind_variations

    def handle_brand_sku(self, sku, brand_rule):
        print(brand_rule)
        cleaned_sku = self.clean_sku(sku)
        sku_format = brand_rule['sku_format']
        base_parts = sku_format['base']
        base_separator = sku_format.get('base_separator', '')
        color_separator = sku_format.get('color_separator', '')

        article_length = int(base_parts['article'][0].split(',')[0])
        model_length = int(base_parts['model'][0].split(',')[0])
        color_length = int(sku_format['color_extension'][0].split(',')[0])

        article_part = cleaned_sku[:article_length]
        model_part = cleaned_sku[article_length:article_length + model_length]
        color_part = cleaned_sku[article_length + model_length:article_length + model_length + color_length]

        # Order: Brand Format with Color, Brand Format without Color
        return [
        article_part + base_separator + model_part + color_separator + color_part + " site:" + brand_rule['domain_hierarchy'][0],
        article_part + base_separator + model_part+ " site:" + brand_rule['domain_hierarchy'][0]
    ]

    def get_indices(self,s):
        non_alnum_indexes = []
        for i, char in enumerate(s):
            if not char.isalnum():
                non_alnum_indexes.append(i)
        return  non_alnum_indexes
    def handle_sku(self,sku,brand):
         return [sku,str(sku) + ' ' + str(brand)]
    def handle_sku_disabled(self,sku,brand):
        indices=self.get_indices(sku)
        variations=[sku,str(sku)+' ' +str(brand)]
        if len(indices)>=4:
            return variations
        elif len(indices)==2:
            article=sku[:indices[0]]
            model=sku[indices[0]+1:indices[1]]
            color=sku[indices[1]+1:]
            variations.append(f"{article} {model} {color}")
            variations.append(f"{article}{model}{color}")
            variations.append(f"{article} {model}")
            variations.append(f"{article}{model}")
            variations.append(f"{article}-{model}")
        #elif len(indices)==1:
        #    article_model=sku[:indices[0]]
        #    color = sku[indices[0] + 1:]
        #    variations.append(f"{article_model} {color}")
        #    variations.append(f"{article_model}{color}")
        #    variations.append(f"{article_model}")

        final_variations=[]
        for variation in variations:
            final_variations.append(variation)
            final_variations.append(f"{variation} {brand}")
        return final_variations
    # def handle_sku(self,sku):
        
    #     sku_len = len(sku)
    #     temp_dict = {}
    #     for i in range(sku_len):
    #         if not sku[i].isalnum():
    #             if not sku[i] in temp_dict:
    #                 temp_dict[sku[i]]=1FilterUrls
    #             else:
    #                 temp_dict[sku[i]]+=1
        
    #     potential_skus=set()
    #     count=0
    #     for key,value in temp_dict.items():
    #         print(key,value)
    #         count+=value
    #         if value<4 and value>1:
    #             temp=sku.split(key)
    #             temp=temp[:-1]
    #             temp=key.join(temp)
    #             potential_skus.add(sku) 
    #             potential_skus.add(self.clean_sku(sku))
    #             potential_skus.add(temp)
    #             potential_skus.add(self.clean_sku(temp))
    #             print([sku,self.clean_sku(sku),temp,self.clean_sku(temp)])
    #         elif value==1:
    #             potential_skus.add(sku)
    #             potential_skus.add(self.clean_sku(sku))
    #             print([sku,self.clean_sku(sku)])
    #     new_skus=set()
    #     if count<4 and count>1:
    #         temp=re.split(r'\W+', sku)
    #         temp=temp[:-1]
    #         temp=" ".join(temp)
    #         potential_skus.add(sku) 
    #         potential_skus.add(self.clean_sku(sku))
    #         potential_skus.add(temp)
    #         potential_skus.add(self.clean_sku(temp))
    #     for variation in potential_skus:
    #         new_skus.add(variation)
    #         new_skus.add(re.sub(r'[^a-zA-Z0-9]', ' ', variation))
    #     return list(new_skus)
       
        
        
        # cleaned_sku = self.clean_sku(sku)

        # article_length = int(sku_format['base']['article'][0].split(',')[0])
        # model_length = int(sku_format['base']['model'][0].split(',')[0])
        # color_length = int(sku_format['color_extension'][0].split(',')[0])

        # article_part = cleaned_sku[:article_length]
        # model_part = cleaned_sku[article_length:article_length + model_length]
        # color_part = cleaned_sku[article_length + model_length:article_length + model_length + color_length]
        # # Order: No space (Article Model Color), Space (Article Model Color), No space (Article Model), Space (Article Model)
        # return [
        #     article_part + model_part + color_part, 
        #     article_part + ' ' + model_part + ' ' + color_part,
        #     article_part + model_part,
        #     article_part + ' ' + model_part
        # ]


    @staticmethod
    def clean_sku(sku):
        sku = str(sku)
        logging.info(f"Cleaning SKU: {sku}")
        cleaned = re.sub(r'[^a-zA-Z0-9]', '', sku)
        logging.info(f"Cleaned SKU: {cleaned}")
        return cleaned


class SearchEngine:
    def __init__(self,variation):
        ###place holder for html body
        self.str_html_body = ""
        self.variation = variation
        self.g_html_response = self.get_google_image_nimble(self.variation)
        print(f"Status Code : {self.g_html_response['status']}")
        
        if self.g_html_response['status'] == 200:
            self.str_html_body = self.g_html_response['body']
            if "Looks like there aren’t any matches for your search" in self.str_html_body:
                print("NO PRODUCT FOUND")
                return None               

            # elif "Looks like there aren’t any matches for your search" not in self.str_html_body:
            #     print('Looking!')

            #     hiQResponse = self.get_original_images(self.str_html_body)[0]
                
            #     Descrip = self.get_original_images(self.str_html_body)[1]
            elif "Looks like there aren’t any matches for your search" not in self.str_html_body and '["GRID_STATE0"' in self.str_html_body:
                print('Looking!')

                hiQResponse = GP(self.str_html_body)[0]
               
                Descrip = GP(self.str_html_body)[1]

                if hiQResponse:
                    self.parsed_results = hiQResponse
                    self.descriptions = Descrip
                    print(f"Parsed Url: {self.parsed_results}\nDescriptions: {self.descriptions}")

                else:
                    print('no descriptions or urls')
                #     self.parsed_results = []
                #     self.descriptions = []
                #     print(f"Parsed Url: {self.parsed_results}\nDescriptions: {self.descriptions}")
            else:
                print('trying again!!!!!!!!!!!!!!!!!!!!!!')
                self.workflow_search(self.variation)


    def workflow_search(self,variation):
        self.g_html_response = self.get_google_image_nimble(self.variation)
        print(f"Status Code : {self.g_html_response['status']}")
        
        if self.g_html_response['status'] == 200:
            self.str_html_body = self.g_html_response['body']
            if "Looks like there aren’t any matches for your search" in self.str_html_body:
                print("NO PRODUCT FOUND")
                return None               
            elif "Looks like there aren’t any matches for your search" not in self.str_html_body and '["GRID_STATE0"' in self.str_html_body:
                print('Looking!')

                hiQResponse = GP(self.str_html_body)[0]
               
                Descrip = GP(self.str_html_body)[1]

                if hiQResponse:
                    self.parsed_results = hiQResponse
                    self.descriptions = Descrip
                    print(f"Parsed Url: {self.parsed_results}\nDescriptions: {self.descriptions}") 

                else:
                    return None
            else:
                print('trying again!!!!!!!')
                self.workflow_search(self.variation)   
            

    def fetch_serverless_no_js_url(self,settings_url, max_retries=3):
        retries = 0
        while retries < max_retries:
            try:
                response = requests.get(settings_url, headers={'User-Agent': 'Mozilla/5.0'})
                if response.status_code == 200:
                    data = response.json()
                    #nimble
                    #serverless_urls = data.get("serverless-urls", {}).get("no_js", [])
                    serverless_urls = data.get("serverless-urls", {}).get("noip_nojs", [])
                    if serverless_urls:
                        return serverless_urls
                retries += 1
                print(f"Retry {retries}/{max_retries} for fetching serverless URLs...")
            except requests.RequestException as e:
                print(f"Failed to fetch serverless URLs: {e}")
                retries += 1
        
        print("Failed to fetch serverless URLs after maximum retries.")
        return []




    # def get_google_image_nimble(self, query):
    #     serverless_urls = self.fetch_serverless_no_js_url(str(SERVERLESS_URL_SETTINGS))
    #     if not serverless_urls:
    #         return {'status': 404, 'body': "Failed to obtain serverless URLs."}
        
    #     attempt_delay = 1  # Start with a 1 second delay
    #     max_attempts = 3
    #     for attempt in range(max_attempts):
    #         func_url = random.choice(serverless_urls)  # Select a URL at random
    #         print(f"Attempt {attempt+1}: Current Url: {func_url}")
    #         headers = {'Content-Type': 'application/json'}

    #         try:
    #             response = requests.get(f'{func_url}?query={query}', headers=headers, timeout=185)
    #             if response.status_code == 200:
    #                 response_json = response.json()
    #                 result = response_json.get('body', None)
    #                 if result:
    #                     return {'status': response.status_code, 'body': self.unpack_content(result)}
    #             else:
    #                 print(f"Request failed with status code: {response.status_code}")
    #         except requests.RequestException as e:
    #             print(f"Error making request: {e}")

    #         time.sleep(attempt_delay)  # Apply the delay
    #         attempt_delay *= 2  # Exponentially increase the delay for the next attempt

    #         # Remove the failed URL from the list to avoid retrying it
    #         serverless_urls.remove(func_url)
    #         if not serverless_urls:  # If we've exhausted all URLs
    #             print("Exhausted all serverless URLs.")
    #             break

    #     return {'status': 404, 'body': "Failed after all attempts."}

    def get_google_image_nimble(self, query):
        serverless_urls = self.fetch_serverless_no_js_url(str(SERVERLESS_URL_SETTINGS))
        if not serverless_urls:
            return {'status': 404, 'body': "Failed to obtain serverless URLs."}
        
        last_used_url = None
        attempt_delay = 1  # Start with a 1 second delay

        for _ in range(len(serverless_urls) * 3):  # Total attempts: thrice the number of serverless URLs
            # Select a random URL avoiding the last used one
            current_urls = [url for url in serverless_urls if url != last_used_url]
            func_url = random.choice(current_urls)

            print(f"Using URL: {func_url}")
            headers = {'Content-Type': 'application/json'}

            try:
                response = requests.get(f'{func_url}?query={query}', headers=headers, timeout=185)
                if response.status_code == 200:
                    response_json = response.json()
                    result = response_json.get('body', None)
                    if result:  # If result is not None, unpack and return
                        return {'status': response.status_code, 'body': self.unpack_content(result)}
                    # If result is None, proceed to retry with a different URL
                else:
                    print(f"Request failed with status code: {response.status_code}")
            except requests.RequestException as e:
                print(f"Error making request: {e}")

            last_used_url = func_url  # Update last used URL
            time.sleep(attempt_delay)  # Apply the delay
            attempt_delay = min(attempt_delay * 2, 60)  # Exponentially increase the delay, up to a max of 60 seconds

        # After trying all URLs without success
        return {'status': 404, 'body': "Failed after all attempts."}


    def unpack_content(self,encoded_content):
        if encoded_content:
            compressed_content = base64.b64decode(encoded_content)
            original_content = zlib.decompress(compressed_content)
            
            return str(original_content)  # Return as binary data
        return None


     
    def send_regular_request_SCRAPERAPI(self, url):
        payload = { 'api_key': 'ab75344fcf729c63c9665e8e8a21d985', 'url': url, 'country_code': 'us'}
    #    payload = { 'api_key': 'ab75344fcf729c63c9665e8e8a21d985', 'url': url}
        r = requests.get('https://api.scraperapi.com/', params=payload,timeout=120)
        return {'status': r.status_code, 'body': r.text}
    #   
    # 
    #!SCRAPER API NEEDS THIS  
    #def search_query(self, sku):
        #query = f"\"{sku}\""
        
        #return f"https://www.google.com/search?q={sku}&newwindow=1&tbm=isch&safe=active"

    # @staticmethod
    # def parse_google_images(html_content):
    #     soup = BeautifulSoup(html_content, 'html.parser')
    #     #soup = BeautifulSoup(html_content, 'lxml')
    #     #  results = []
    #     #  for g in soup.find_all('div', class_='g'):
    #     #      links = g.find_all('a')
    #     #      if links and 'href' in links[0].attrs:  # check if 'href' attribute exists
    #     #          results.append(links[0]['href'])
    #     return soup
    
    # def get_original_images(self,html):
    #     soup = BeautifulSoup(html, 'html.parser')
    #     all_script_tags = soup.select("script") 
    #     # Extract matched images data
    #     matched_images_data = "".join(re.findall(r"AF_initDataCallback\(([^<]+)\);", str(all_script_tags)))
    #     #matched_images_data = "".join(re.findall(r"AF_initDataCallback\(({key: 'ds:1'.*?)\);</script>", str(all_script_tags)))
    #     print(matched_images_data)
    #     matched_images_data_fix = json.dumps(matched_images_data)
    #     print(matched_images_data)
    #     matched_images_data_json = json.loads(matched_images_data_fix)
    #     print(matched_images_data_json)
    #     matched_google_image_data = re.findall(r'\"b-GRID_STATE0\"(.*)sideChannel:\s?{}}', matched_images_data_json)
    #     print(matched_google_image_data)
    #     # Extract thumbnails
    #     matched_google_images_thumbnails = ", ".join(
    #         re.findall(r'\[\"(https\:\/\/encrypted-tbn0\.gstatic\.com\/images\?.*?)\",\d+,\d+\]',
    #                 str(matched_google_image_data))).split(", ")
    #     print(matched_google_images_thumbnails)
    #     thumbnails = [
    #         bytes(bytes(thumbnail, "ascii").decode("unicode-escape"), "ascii").decode("unicode-escape") for thumbnail in matched_google_images_thumbnails
    #     ]
    #     ##########
    #     print('thumbnails')
    #     print(thumbnails)
    #     removed_matched_google_images_thumbnails = re.sub(
    #         r'\[\"(https\:\/\/encrypted-tbn0\.gstatic\.com\/images\?.*?)\",\d+,\d+\]', "", str(matched_google_image_data))  
    #     # Extract full resolution images
    #     matched_google_full_resolution_images = re.findall(r"(?:'|,),\[\"(https:|http.*?)\",\d+,\d+\]", removed_matched_google_images_thumbnails)   
    #     full_res_images = [
    #         bytes(bytes(img, "ascii").decode("unicode-escape"), "ascii").decode("unicode-escape") for img in matched_google_full_resolution_images
    #     ]   
    #     # Assume descriptions are extracted
    #     descriptions = LR().get(soup, '"2008":[null,"', '"]}],null,') # Replace 'description_pattern' with your actual regex pattern for descriptions   
    #     final_thumbnails = []
    #     final_full_res_images = []
    #     final_descriptions = [] 
    #     # Iterate over each thumbnail
    #     for i, thumbnail in enumerate(thumbnails):
    #         try:
    #             # If a full resolution image exists, add it. If not, add the thumbnail instead.
    #             final_thumbnails.append(thumbnail)
    #             final_full_res_images.append(full_res_images[i] if i < len(full_res_images) else thumbnail)
    #             final_descriptions.append(descriptions[i])
    #         except IndexError:
    #             # If there is an index error, it means a description could not be found for the current thumbnail. So skip this thumbnail.
    #             continue    
    #     return final_full_res_images, final_descriptions,final_thumbnails   

    # def get_original_images(self, html):
    #     #rstring = self.generate_random_name()
    #     print('---html start---')
    #     print(html)
    #     print('---html end---')
    #     #filepath = str(rstring)+'.txt'
    #     #with open(filepath, 'w') as file:
    #         #file.write(str(html))
    #     matched_images_data = "".join(re.findall(r"AF_initDataCallback\(([^<]+)\);", str(html)))

    #     matched_images_data_fix = json.dumps(matched_images_data)
    #     matched_images_data_json = json.loads(matched_images_data_fix)

    #     matched_google_image_data = re.findall(r'\"b-GRID_STATE0\"(.*)sideChannel:\s?{}}', matched_images_data_json)

    #     # Extract thumbnails
    #     matched_google_images_thumbnails = ", ".join(
    #         re.findall(r'\[\"(https\:\/\/encrypted-tbn0\.gstatic\.com\/images\?.*?)\",\d+,\d+\]',
    #                 str(matched_google_image_data))).split(", ")

    #     thumbnails = [
    #         bytes(bytes(thumbnail, "ascii").decode("unicode-escape"), "ascii").decode("unicode-escape") for thumbnail in matched_google_images_thumbnails
    #     ]
        
    #     removed_matched_google_images_thumbnails = re.sub(
    #         r'\[\"(https\:\/\/encrypted-tbn0\.gstatic\.com\/images\?.*?)\",\d+,\d+\]', "", str(matched_google_image_data))

    #     # Extract full resolution images
    #     matched_google_full_resolution_images = re.findall(r"(?:'|,),\[\"(https:|http.*?)\",\d+,\d+\]", removed_matched_google_images_thumbnails)

    #     full_res_images = [
    #         bytes(bytes(img, "ascii").decode("unicode-escape"), "ascii").decode("unicode-escape") for img in matched_google_full_resolution_images
    #     ]

    #     # Assume descriptions are extracted
    #     descriptions = LR().get(html, '"2008":[null,"', '"]}],null,') # Replace 'description_pattern' with your actual regex pattern for descriptions
    #     #descriptions = []
    #     final_thumbnails = []
    #     final_full_res_images = []
    #     final_descriptions = []
    #     # Iterate over each thumbnail
    #     for i, thumbnail in enumerate(thumbnails):
    #         try:
    #             # If a full resolution image exists, add it. If not, add the thumbnail instead.
    #             final_thumbnails.append(thumbnail)
    #             if i < len(full_res_images) and full_res_images[i] != '':
    #                 final_full_res_images.append(full_res_images[i])
    #             else:
    #                 final_full_res_images.append(thumbnail)
    #             final_descriptions.append(descriptions[i])
    #         except IndexError:
    #             # If there is an index error, it means a description could not be found for the current thumbnail. So skip this thumbnail.
    #             continue


    #     print(f"Thumbs\n____________________________\n{final_thumbnails}\n-----------------------------------")
    #     print(f"Full REs\n____________________________\n{final_full_res_images}\n-----------------------------------")
    #     print(f"Final Desc\n____________________________\n{final_descriptions}\n-----------------------------------")

    #     return final_full_res_images, final_descriptions,final_thumbnails


from urllib.parse import urlparse
from itertools import product
class FilterUrls:
    def __init__(self, url_dicts, brand, sku):
        self.whitelisted_domains = [
            "fwrd.com",
            "modesens.com",
            "saksfifthavenue.com",
            "saksoff5th.com",
            "nordstrom.com",
            "nordstromrack.com",
            "giglio.com",
            "italist.com",
            "farfetch.com",
            "mytheresa.com",
            "neimanmarcus.com",
            "jomashop.com",
            "vitkac.com",
            "goat.com",
            "thebestshops.com",
        ]
        self.prepared_whitelisted_domains = [domain.replace('www.', '') for domain in self.whitelisted_domains]
        self.brand = brand.lower()
        self.sku = sku.lower()
        self.url_dicts_nodups = self.remove_dups(url_dicts)

        self.filtered_result = self.filter_image_dict(self.url_dicts_nodups)
        
        
        #self.filtered_url_dicts = self.filter_urls(self.url_dicts_nodups)


    def get_brand_names(self,brand):
        brand_settings = BrandSettings(json.loads(open(BRANDSETTINGSPATH,encoding='utf-8').read())).get_brand_img_names(brand)
        return brand_settings  

    def get_indices(self,s):
            non_alnum_indexes = []
            for i, char in enumerate(s):
                if not char.isalnum():
                    non_alnum_indexes.append(i)
            return  non_alnum_indexes
    def split_string_at_indices(self,s, indices):
        # Initialize the start index and the list to store the segments
        start = 0
        segments = []

        # Iterate through each index in the indices list
        for index in indices:
            # Add the substring from the current start index to the current index
            segments.append(s[start:index])
            # Update the start index for the next segment
            start = index+1

        # Add the remaining part of the string as the last segment
        segments.append(s[start:])

        return segments


    def segment_sku(self,sku, brand):
        print("pre strip ",sku)
        sku = sku.replace(brand, "")
        print("after strip ",sku)
        indices=self.get_indices(sku)
        print(len(indices))
        if len(indices) < 2:
            return [sku]               
        print("indices ",indices)
        segments = self.split_string_at_indices(sku,indices) 
        print("segments ",segments)
        final_segments=[]
        for segment in segments:
            if segment!="":
                final_segments.append(segment)
        print("Final Segments ",final_segments)
        return final_segments
    def sublists(self,lst):
        result = []
        for doslice in product([True, False], repeat=len(lst) - 1):
            slices = []
            start = 0
            for i, slicehere in enumerate(doslice, 1):
                if slicehere:
                    slices.append(lst[start:i])
                    start = i
            slices.append(lst[start:])
            result.append(slices)  # Collect slices into a result list
        return result  # Return the result list instead of using yielddef sublists(lst):

    def clean_sublist(self,sublists):
        # Initialize a list to store the processed sublists
        processed_sublists = []

        # Iterate directly over sublists
        for s_list in sublists:
            # Check if the current sublist has exactly 3 elements
            if len(s_list) == 3:
                # Initialize a new list for the current sublist, to hold combined strings
                new_sublist = []
                # Iterate over each inner list in the current sublist
                for inner_list in s_list:
                    # Combine the elements of the inner list into a single string
                    combined_string = ''.join(inner_list)
                    # Add the combined string as a new single-element list
                    new_sublist.append([combined_string])
                # Add the newly formed sublist to the processed_sublists list
                processed_sublists.append(new_sublist)

        # Return the list of processed sublists
        return processed_sublists
    def filter_sublists_by_length(self,result):
        # Initialize a list to store sublists that meet the criteria
        filtered_list = []

        # Iterate over each sublist in the result
        for sublist in result:
            # Check if the concatenated string length in the first two lists is greater than 3
            if len(''.join(sublist[0])) >= 3 and len(''.join(sublist[1])) >= 3:
                # If both conditions are met, append the sublist to the filtered list
                filtered_list.append(sublist)

        # Return the filtered list
        return filtered_list
    def transform_sublist(self,input_list):
        # Initialize an empty list to hold the result
        result = []

        # Iterate through each item in the input list
        for item in input_list:
            # Assuming each item has exactly three lists corresponding to article, model, and color
            article, model, color = item

            # Create a dictionary for the current item
            current_dict = {
                "article": article[0],  # Extract the first (and only) element from the list
                "model": model[0],      # Extract the first (and only) element from the list
                "color": color[0]       # Extract the first (and only) element from the list
            }

            # Add the dictionary to the result list
            result.append(current_dict)

        return result



    def segment_workflow(self,sku, brand):
        # Step 1: Segment the SKU
        segments = self.segment_sku(sku, brand)
        print(segments)
        if len(segments) < 3:
            return [{'full_sku': str(sku.replace(brand, ""))}]
        sublists_list = list(self.sublists(segments))
        result = self.clean_sublist(sublists_list)
        
        # Step 4: Filter sublists by length
        filtered_result = self.filter_sublists_by_length(result)

        # Step 5: Transform the filtered sublists
        final_result = self.transform_sublist(filtered_result)
        print(final_result)
        return final_result







    def clean_string(self, input_string):
        # Remove all non-alphanumeric characters except spaces using regex
        cleaned = re.sub(r'[^a-zA-Z0-9 ]+', '', input_string)
        
        # Replace multiple spaces with a single space
        cleaned = ' '.join(cleaned.split())

        # Convert to lowercase and strip whitespace from the ends
        cleaned = cleaned.lower().strip()
        return cleaned


    def fetch_json_from_url(self,url):
        try:
            response = requests.get(url)
            json_body = response.text
            response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
            json_data = json.loads(json_body)
            print(type(json_data))
            return json_data
        except requests.exceptions.RequestException as e:
            print(f"Error fetching JSON from URL: {e}")
            return None



    def remove_duplicates(self,lst):
        seen = set()
        new_lst = []
        for item in lst:
            if item not in seen:
                new_lst.append(item)
                seen.add(item)
        return new_lst

    def get_score_1(self,url:str,description:str, sku:str,brand:str, point_dict:dict):
            possible_amc=self.segment_workflow(sku,brand)
    
            brand_names_unclean = self.get_brand_names(brand)
            
            if brand_names_unclean:
            
                brand_names = [self.clean_string(brand) for brand in brand_names_unclean]
                brand_names = self.remove_duplicates(brand_names)
                print(f"This is the brand names {brand_names}")
            else:
                brand_names = [brand]           
            print(f"This is the brand names {brand_names}")
            possible_scores=[]
            print(f"This is the possible scores {possible_scores}")
            current_score=0
            print(f"This is the current scores {current_score}")
            article_score_value=point_dict["article"] #change these values as needed
            model_score_value=point_dict["model"] #change these values as needed
            color_score_value=point_dict["color"] #change these values as needed
            brand_score_value=point_dict["brand"] #change these values as needed
            threshold=point_dict["threshold"] #change these values as needed
            print(f"This is the threshold {threshold}")
            
            url=self.clean_string(url)
            description=self.clean_string(description)
            fullsku = possible_amc[0].get('full_sku',None)
            if fullsku:

                for amc_dict in possible_amc:
                    current_score = 0
                    for value in amc_dict.values():
                        print("value ",value)
                        value=self.clean_string(value)
                        if value in url:
                                print(f"Got a point for {value} in url {url}")
                                current_score+=1 
                        if value in description:
                                print(f"Got a point for {value} in description{description}")
                                current_score+=1
                    for brand in brand_names:
                        brand=self.clean_string(brand)
                        if brand in url:
                            print(f"Got a point for {brand}")
                            current_score+=brand_score_value
                        elif brand in description:
                            print(f"Got a point for {brand}")
                            current_score+=brand_score_value
                        
                
                    possible_scores.append(current_score)
                    print(f"This score: {current_score} came from this dict {amc_dict}")
                #print(f"These are all the possible scores {possible_scores}")
                #filtered_scores = [score for score in possible_scores if score >= threshold]
                # return filtered_scores

                
                

            else:   
                for amc_dict in possible_amc:
                    print(amc_dict)
                    for key,value in amc_dict.items():
                        value=self.clean_string(value)
                        print(f"This is the new value {value}")
                        if key=="article":
                            if value in url:
                                print(f"Got a point for {value}")
                                current_score+=article_score_value 
                            if value in description:
                                print(f"Got a point for {value}")
                                current_score+=article_score_value
                        elif key=="model":
                            if value in url:
                                print(f"Got a point for {value}")
                                current_score+=model_score_value 
                            if value in description:
                                print(f"Got a point for {value}")
                                current_score+=model_score_value
                        elif key=="color":
                            if value in url:
                                print(f"Got a point for {value}")
                                current_score+=color_score_value 
                            if value in description:
                                print(f"Got a point for {value}")
                                current_score+=color_score_value
                        
                    for brand in brand_names:
                        brand=self.clean_string(brand)
                        if brand in url:
                            print(f"Got a point for {brand}")
                            current_score+=brand_score_value
                        elif brand in description:
                            print(f"Got a point for {brand}")
                            current_score+=brand_score_value
                        
                
                    possible_scores.append(current_score)
                    print(f"This score: {current_score} came from this dict {amc_dict}")
                    current_score=0

                print(f"These are all the possible scores {possible_scores}")
                filtered_scores=[]
                for score in possible_scores:
                    if score>=threshold:
                        filtered_scores.append(score)
                        
                return filtered_scores
        
    
    def get_score_2(self,url: str, description: str, sku: str, brand: str, point_dict: dict):
        possible_amc=self.segment_workflow(sku,brand)

        brand_names_unclean = self.get_brand_names(brand)
        if brand_names_unclean:
        
            brand_names = [self.clean_string(brand) for brand in brand_names_unclean]
            brand_names = self.remove_duplicates(brand_names)
            print(f"This is the brand names {brand_names}")
        else:
            brand_names = [brand]
        possible_scores = []
        article_model_score_value = point_dict["article"] # change this key
        color_score_value = point_dict["color"]
        brand_score_value = point_dict["brand"]
        threshold = point_dict["threshold"]
        url = self.clean_string(url)
        description = self.clean_string(description)
        if possible_amc:
            fullsku = possible_amc[0].get('full_sku',None)
            if fullsku:
                for amc_dict in possible_amc:
                    current_score = 0
                    for value in amc_dict.values():
                        print("value ",value)
                        value=self.clean_string(value)
                        if value in url:
                                print(f"Got a point for {value} in url {url}")
                                current_score+=0.5 
                        if value in description:
                                print(f"Got a point for {value} in description{description}")
                                current_score+=1
                    for brand in brand_names:
                        brand=self.clean_string(brand)
                        print(brand)
                        if brand in url:
                            print(f"Got a point for {brand} Value: {brand_score_value}")
                            print(url)
                            current_score+=brand_score_value
                        elif brand in description:
                            print(f"Got a point for {brand} Value: {brand_score_value}")
                            current_score+=brand_score_value
                        
                
                    possible_scores.append(current_score)
                    print(f"This score: {current_score} came from this dict {amc_dict}")
                print(f"These are all the possible scores {possible_scores}")
                if len(possible_scores)==1 and possible_scores[0]>=threshold:
                    return possible_scores
                else:
                    ##FILTERRRRRRR
                    filtered_scores = [score for score in possible_scores if score >= threshold]
                    if len(filtered_scores)==0:
                        return filtered_scores
                    else:
                        filtered_scores = filtered_scores.sort(reverse=True)
                        print(filtered_scores, '----- filtered scores')
                        return filtered_scores
    
    
            
            
    
            else:
                for amc_dict in possible_amc:
                    print(amc_dict)
                    current_score = 0
                    article_present = model_present = False
    
                    for key, value in amc_dict.items():
                        value = self.clean_string(value)
                        print(f"This is the new value {value}")
                        if key == "article" and (value in url or value in description):
                            article_present = True
                            print(f"article present {value}")
                        elif key == "model" and (value in url or value in description):
                            model_present = True
                            print(f"model present {value}")
    
                    # If both article and model are present, award points for them
                    if article_present and model_present:
                        current_score += article_model_score_value
                        #print(f"article and model are present {value}")
                        # Check for color only if article and model are present
                        color_value = self.clean_string(amc_dict.get("color", ""))
                        if color_value and (color_value in url or color_value in description):
                            print(f"Got a point for {color_value}")
                            current_score += color_score_value
    
                    # Check for brand independently
                    brand_score_added = False
                    for brand in brand_names:
                        brand = self.clean_string(brand)
                        if brand in url or brand in description:
                            if not brand_score_added:  # Ensure we only add the brand score once
                                print(f"Got a point for {brand} Value: {brand_score_value}")
                                current_score += brand_score_value
                                brand_score_added = True
    
                    possible_scores.append(current_score)
                    print(f"This score: {current_score} came from this dict {amc_dict}")
    
                print(f"These are all the possible scores {possible_scores}")
                if len(possible_scores)==1 and possible_scores[0]>=threshold:
                    return possible_scores
                else:
                    ##FILTERRRRRRR
                    filtered_scores = [score for score in possible_scores if score >= threshold]
                    if len(filtered_scores)==0:
                        return filtered_scores
                    else:
                        filtered_scores = filtered_scores.sort(reverse=True)
                        print(filtered_scores, '----- filtered scores')
                        return filtered_scores
        else:
            # Return an empty list when possible_amc is empty or None
            return []
        return possible_scores



    def get_domain(self,url: str) -> str:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        return domain
    def get_score_3(self, url:str, brand_domains:list[str], json_domains:dict):
        #if brand_domains:
        #    for brand_domain in brand_domains:
        #        if brand_domain in self.get_domain(url):
        #            return 100000000
        domain_score=0
        url=self.clean_string(url)
        for domain, score in json_domains.items(): # Use .items() to get both keys (domains) and values (scores)
            print(json_domains)
            domain=self.clean_string(domain)
            if domain in self.get_domain(url):
                domain_score += score
        return domain_score



    def filter_image_dict(self,image_urls_dict:list[dict]):
        #json_url_1="https://raw.githubusercontent.com/nikiconluxury/images-filter/main/step_1_filter_images.json"
        json_url_2="https://raw.githubusercontent.com/nikiconluxury/images-filter/main/step_2_filter_images.json"
        json_url_3="https://raw.githubusercontent.com/nikiconluxury/images-filter/main/domain_point_values.json"
        #json_dict_1=self.fetch_json_from_url(json_url_1)
        json_dict_2=self.fetch_json_from_url(json_url_2)
        json_dict_3=self.fetch_json_from_url(json_url_3)
        
        # first_pass=[]
        # for image_dict in image_urls_dict:
        #     url=image_dict["url"]
        #     description=image_dict["description"]
        #     sku=image_dict["sku"]
        #     brand=image_dict["brand"]
        #     if len(self.get_score_1(url, description, sku, brand, json_dict_1))>0:
        #         first_pass.append(image_dict)
        # if len(first_pass)==0:
        #     return "this was a garbage data set"
        # elif len(first_pass)==1:
        #     print('only one item passed tier 1 of filter')
        #     return first_pass[0]
        
        second_pass=[]
        #for image_dict in first_pass:
        for image_dict in image_urls_dict:
            if image_dict:
                url=image_dict["url"]
                description=image_dict["description"]
                sku=image_dict["sku"]
                brand=image_dict["brand"]
                if len(self.get_score_2(url, description, sku, brand, json_dict_2))>0:
                    second_pass.append(image_dict)
            else:
                print('encountered none object in image_urls_dict')
                print(image_urls_dict)
        if len(second_pass)==0:
            #return first_pass
            return 'None found in this filter'
        elif len(second_pass)>=1:
            return second_pass[0]
        
        # #third_pass=[]
        # for image_dict in second_pass:
        #     if image_dict:
        #         url=image_dict["url"]
        #         brand_domains=image_dict["brand_domains"]
        #         final_score=self.get_score_3(url, brand_domains, json_dict_3)
        #         if not final_score:
        #             return second_pass[0]
        #         if final_score>0:
        #             third_pass.append(image_dict)
        #             image_dict["score"]=final_score
        #     else:
        #         print('encountered none object in second_pass')
        #         print(image_urls_dict)
        # # if len(third_pass)==0:
        # #     return second_pass[0]
        # # highest_score=0
        # # for index,image_dict in enumerate(third_pass):
        # #     if image_dict["score"]>highest_score:
        # #         highest_score=image_dict["score"]
        # #         final_index=index
        # # return third_pass[final_index]

    
    

    def filter_image_dict_2(self,image_urls_dict:list[dict]):
        first_pass=[]
        for image_dict in image_urls_dict:
            url=image_dict["url"]
            description=image_dict["description"]
            sku=image_dict["sku"]
            brand=image_dict["brand"]

    













    # def filter_urls(self, url_dicts):
    #     filtered_url_dicts = []
    #     for url_dict in url_dicts:
    #         original_url = url_dict['url'].strip()
    #         url = original_url
    #         if not url.startswith(('http://', 'https://')):
    #             url = 'http://' + url
            
    #         domain = urlparse(url).netloc.lower()
    #         print(f"Original URL: {original_url}, Domain: {domain}")

    #         if domain.startswith('www.'):
    #             domain = domain[4:]
    #         print(f"Cleaned Domain: {domain}")

    #         if self.sku in url.lower():
    #             reason = "SKU match"
    #         elif self.brand in url.lower():
    #             reason = "Brand match"
    #         elif domain in self.prepared_whitelisted_domains:
    #             reason = "Whitelist match"
    #         else:
    #             reason = None
            
    #         if reason:
    #             print(f"Included: {url}, Reason: {reason}")
    #             filtered_url_dicts.append(url_dict)
    #         else:
    #             print(f"Excluded: {url}, Reason: Not matched")

    #     return filtered_url_dicts
    def filter_urls(self, url_dicts):
        filtered_url_dicts = []
        for url_dict in url_dicts:
            url = url_dict['url'].strip()
            if not url.startswith(('http://', 'https://')):
                url = 'http://' + url
            
            domain = urlparse(url).netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Initialize reason as None
            reason = None

            # Adjusting domain matching to include subdomains of whitelisted domains
            domain_matched = any(domain == wl_domain or domain.endswith('.' + wl_domain) for wl_domain in self.prepared_whitelisted_domains)

            if self.sku in url.lower():
                reason = "sku"
            elif self.brand in url.lower():
                reason = "brand"
            elif domain_matched:
                #########! WHITELISTED DOMAIN
                
                reason = "whitelist"
            
            if reason:
                # Add the reason (type) to the url_dict
                modified_url_dict = url_dict.copy()  # Create a copy to avoid modifying the original dict
                modified_url_dict['type'] = reason
                print(f"Included: {url}, Reason: {reason}")
                filtered_url_dicts.append(modified_url_dict)
            else:
                print(f"Excluded: {url}, Reason: Not matched")

        return filtered_url_dicts


    def remove_dups(self, url_dicts):
        seen = set()
        new_list = []
        for url_dict in url_dicts:
            if url_dict['url'] not in seen:
                seen.add(url_dict['url'])
                new_list.append(url_dict)
        return new_list
class SearchEngineV2:


    def get_results(self, variation):
        self.workflow_results = self.search_workflow(variation)
        if self.workflow_results:
            urls_list = self.workflow_results[0]
            descriptions_list=self.workflow_results[1]
            return urls_list,descriptions_list


    
    def search_workflow(self, variation):
        html=self.get_html(variation)
        if html["status"]!=200:
            self.search_workflow(variation)
        else:
            html_body=html["body"]

            if 'FINANCE",[22,1]]]]]' in html_body:
                if '"2003":' not in html_body:
                    print('no images found')
                    my_list = [['no images found'],['no description found']]
                    return my_list
                else:
                    print("parsing........")
                    search_results = GP(html_body)
                    print(f"{search_results}")
                    urls_list=search_results[0]
                    descriptions_list=search_results[1]    
                    #print(f"{urls_list}\n------{descriptions_list}\nXXXXXXXX")      
                    if not urls_list:
                        print('no urls list')
                        self.search_workflow(variation)
                    elif not descriptions_list:
                        print('no desc list')
                        self.search_workflow(variation)
                    else:
                        clean_urls = self.clean_strings(urls_list)
                        clean_descriptions = self.clean_strings(descriptions_list)
                        if clean_urls and clean_descriptions:
                            print(clean_urls)
                            print(clean_descriptions)
                            my_list=[clean_urls,clean_descriptions]
                            return my_list
                        else:
                            return [urls_list,descriptions_list]

            else:
                print('GRID_STATE0'," NOT FOUND")
                self.search_workflow(variation)


    def clean_strings(self,strings):
        cleaned_strings = []
        for s in strings:
            try:
                # Normalize string to Unicode NFKC (Normalization Form KC)
                # NFKC combines characters and applies compatibility decompositions,
                # which can help in standardizing characters and removing certain types of problematic characters.
                cleaned = unicodedata.normalize('NFKC', s)

                # Optionally, here you can also remove or replace specific characters 
                # that are known to be problematic for your application.
                # For example, replacing non-breaking spaces with normal spaces:
                cleaned = cleaned.replace('\u00A0', ' ')

                cleaned_strings.append(cleaned)
            except Exception as e:
                # Log or handle any exceptions raised during the process
                print(f"Error cleaning string {s}: {e}")
                # Add the original string if there was an error
                cleaned_strings.append(s)
        return cleaned_strings

    def fetch_serverless_no_js_url(self,settings_url, max_retries=3):
        retries = 0
        while retries < max_retries:
            try:
                response = requests.get(settings_url, headers={'User-Agent': 'Mozilla/5.0'})
                if response.status_code == 200:
                    data = response.json()
                    #nimble
                    #serverless_urls = data.get("serverless-urls", {}).get("no_js", [])
                    serverless_urls = data.get("serverless-urls", {}).get("noip_nojs", [])
                    if serverless_urls:
                        return serverless_urls
                retries += 1
                print(f"Retry {retries}/{max_retries} for fetching serverless URLs...")
            except requests.RequestException as e:
                print(f"Failed to fetch serverless URLs: {e}")
                retries += 1
        
        print("Failed to fetch serverless URLs after maximum retries.")
        return []
    def get_html(self, query):
        serverless_urls = self.fetch_serverless_no_js_url(str(SERVERLESS_URL_SETTINGS))
        if not serverless_urls:
            return {'status': 404, 'body': "Failed to obtain serverless URLs."}
        
        last_used_url = None
        attempt_delay = 1  # Start with a 1 second delay

        for _ in range(len(serverless_urls) * 3):  # Total attempts: thrice the number of serverless URLs
            # Select a random URL avoiding the last used one
            current_urls = [url for url in serverless_urls if url != last_used_url]
            func_url = random.choice(current_urls)

            print(f"Using URL: {func_url}")
            
            headers = {'Content-Type': 'application/json'}

            try:
                response = requests.get(f'{func_url}?query={query}', headers=headers, timeout=185)
                if response.status_code == 200:
                    print(response.status_code)
                    response_json = response.json()
                    result = response_json.get('body', None)
                    if result:  # If result is not None, unpack and return
                        return {'status': response.status_code, 'body': self.unpack_content(result)}
                    # If result is None, proceed to retry with a different URL
                else:
                    print(f"Request failed with status code: {response.status_code}")
            except requests.RequestException as e:
                print(f"Error making request: {e}")

            last_used_url = func_url  # Update last used URL
            time.sleep(attempt_delay)  # Apply the delay
            attempt_delay = min(attempt_delay * 2, 60)  # Exponentially increase the delay, up to a max of 60 seconds

        # After trying all URLs without success
        return {'status': 404, 'body': "Failed after all attempts."}


    def unpack_content(self,encoded_content):
        if encoded_content:
            compressed_content = base64.b64decode(encoded_content)
            original_content = zlib.decompress(compressed_content)
            # with open('text.html', 'w') as file:
            #     file.write(str(original_content))
            return str(original_content)  # Return as binary data
        return None
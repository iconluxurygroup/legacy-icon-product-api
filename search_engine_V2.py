# from google_parser import get_original_images as GP
# class SearchEngineV2:

#     def __init__(self, variation):
#         self.urls_list,descriptions_list=self.search_workflow(variation)
    
#     def search_workflow(self, variation):
#         html=get_html(variation)
#         if html["status"]!=200:
#             self.search_workflow(variation)
#         else:
#             html_body=html["body"]
#             if '["GRID_STATE0"' in html_body:
#                 print("parsing........")
#                 urls_list=GP(html_body)[0]
#                 descriptions_list=GP(html_body)[1]          
#                 if not urls_list or not descriptions_list:
#                     self.search_workflow(variation)
#                 else:
#                     return urls_list,descriptions_list
#             else:
#                 self.search_workflow(variation)


#     def fetch_serverless_no_js_url(self,settings_url, max_retries=3):
#         retries = 0
#         while retries < max_retries:
#             try:
#                 response = requests.get(settings_url, headers={'User-Agent': 'Mozilla/5.0'})
#                 if response.status_code == 200:
#                     data = response.json()
#                     #nimble
#                     #serverless_urls = data.get("serverless-urls", {}).get("no_js", [])
#                     serverless_urls = data.get("serverless-urls", {}).get("noip_nojs", [])
#                     if serverless_urls:
#                         return serverless_urls
#                 retries += 1
#                 print(f"Retry {retries}/{max_retries} for fetching serverless URLs...")
#             except requests.RequestException as e:
#                 print(f"Failed to fetch serverless URLs: {e}")
#                 retries += 1
        
#         print("Failed to fetch serverless URLs after maximum retries.")
#         return []
#     def get_html(self, query):
#         serverless_urls = self.fetch_serverless_no_js_url(str(SERVERLESS_URL_SETTINGS))
#         if not serverless_urls:
#             return {'status': 404, 'body': "Failed to obtain serverless URLs."}
        
#         last_used_url = None
#         attempt_delay = 1  # Start with a 1 second delay

#         for _ in range(len(serverless_urls) * 3):  # Total attempts: thrice the number of serverless URLs
#             # Select a random URL avoiding the last used one
#             current_urls = [url for url in serverless_urls if url != last_used_url]
#             func_url = random.choice(current_urls)

#             print(f"Using URL: {func_url}")
#             headers = {'Content-Type': 'application/json'}

#             try:
#                 response = requests.get(f'{func_url}?query={query}', headers=headers, timeout=185)
#                 if response.status_code == 200:
#                     response_json = response.json()
#                     result = response_json.get('body', None)
#                     if result:  # If result is not None, unpack and return
#                         return {'status': response.status_code, 'body': self.unpack_content(result)}
#                     # If result is None, proceed to retry with a different URL
#                 else:
#                     print(f"Request failed with status code: {response.status_code}")
#             except requests.RequestException as e:
#                 print(f"Error making request: {e}")

#             last_used_url = func_url  # Update last used URL
#             time.sleep(attempt_delay)  # Apply the delay
#             attempt_delay = min(attempt_delay * 2, 60)  # Exponentially increase the delay, up to a max of 60 seconds

#         # After trying all URLs without success
#         return {'status': 404, 'body': "Failed after all attempts."}


#     def unpack_content(self,encoded_content):
#         if encoded_content:
#             compressed_content = base64.b64decode(encoded_content)
#             original_content = zlib.decompress(compressed_content)
#             return str(original_content)  # Return as binary data
#         return None


     
#     def send_regular_request_SCRAPERAPI(self, url):
#         payload = { 'api_key': 'ab75344fcf729c63c9665e8e8a21d985', 'url': url, 'country_code': 'us'}
#     #    payload = { 'api_key': 'ab75344fcf729c63c9665e8e8a21d985', 'url': url}
#         r = requests.get('https://api.scraperapi.com/', params=payload,timeout=120)
#         return {'status': r.status_code, 'body': r.text}
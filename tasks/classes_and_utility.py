import json,re,requests,logging
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from settings import BRANDSETTINGSPATH

# class BrandSettings:
#     def __init__(self, settings):
#         self.settings = settings

#     def get_rules_for_brand(self, brand_name):
#         for rule in self.settings['brand_rules']:
#             if brand_name in rule['names']:
#                 return rule
#         return None
class BrandSettings:
    def __init__(self, settings):
        self.settings = settings

    def get_rules_for_brand(self, brand_name):
        # Convert brand_name to lowercase for case-insensitive comparison
        brand_name_lower = brand_name.lower()
        for rule in self.settings['brand_rules']:
            # Convert each name in rule['names'] to lowercase and check if brand_name_lower is among them
            if brand_name_lower in [name.lower() for name in rule['names']]:
                return rule
        return None
    def get_brand_img_domains(self, brand_name):
        # Convert brand_name to lowercase for case-insensitive comparison
        brand_rules = self.get_rules_for_brand(brand_name)
        if brand_rules:
            return brand_rules.get('image_domain', [])
        else:
            return None

    def get_brand_img_names(self, brand_name):
        # Convert brand_name to lowercase for case-insensitive comparison
        brand_rules = self.get_rules_for_brand(brand_name)
        if brand_rules:
            return brand_rules.get('names', [])
        else:
            return None
    #FETCH SETTINGS REMOTELY FROM S3 or wtv.
    # def fetch_remote_config(url):
        # response = requests.get(url)
        # if response.status_code == 200:
            # return response.json()
        # else:
            # print(f"Failed to fetch remote config: {response.status_code}")
            # return None

    # remote_config_url = "https://example.com/config.json"
    # config = fetch_remote_config(remote_config_url)
    # if config:
        # print("Remote config fetched successfully:")
        # print(config)
    # else:
        # print("Failed to fetch remote config.")
    
class SKUManager:
    def __init__(self, brand_settings,sku, brand):
        self.settings_for_brand = brand_settings.get_rules_for_brand(brand)
        self.variations=self.generate_variations(sku, self.settings_for_brand)
    
    def generate_variations(self, input_sku, brand_rule):
        if brand_rule:
            brand_variations = self.handle_brand_sku(input_sku, brand_rule)
            blind_variations = self.handle_sku(input_sku, brand_rule)
            return brand_variations + blind_variations# + [input_sku]
        else:
            return None

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

    def handle_sku(self, sku, brand_rule):
        cleaned_sku = self.clean_sku(sku)
        sku_format = brand_rule['sku_format']

        article_length = int(sku_format['base']['article'][0].split(',')[0])
        model_length = int(sku_format['base']['model'][0].split(',')[0])
        color_length = int(sku_format['color_extension'][0].split(',')[0])

        article_part = cleaned_sku[:article_length]
        model_part = cleaned_sku[article_length:article_length + model_length]
        color_part = cleaned_sku[article_length + model_length:article_length + model_length + color_length]

        # Order: No space (Article Model Color), Space (Article Model Color), No space (Article Model), Space (Article Model)
        return [
            article_part + model_part + color_part, 
            article_part + ' ' + model_part + ' ' + color_part,
            article_part + model_part,
            article_part + ' ' + model_part
        ]


    @staticmethod
    def clean_sku(sku):
        sku = str(sku)
        logging.info(f"Cleaning SKU: {sku}")
        cleaned = re.sub(r'[^a-zA-Z0-9]', '', sku)
        logging.info(f"Cleaned SKU: {cleaned}")
        return cleaned
    
class SearchEngine:
    def __init__(self,variation):
        #self.user_agents = user_agents
        self.parsed_results = []
        self.variation = variation
        self.query_url = self.create_brand_search_query(variation)
        self.g_html_response = self.send_regular_request(self.query_url)
        if self.g_html_response['status'] == 200:
            self.parsed_results = self.parse_google_results(self.g_html_response['body'])
     
     
    def send_regular_request(self, url):
        payload = { 'api_key': 'ab75344fcf729c63c9665e8e8a21d985', 'url': url, 'country_code': 'us'}
    #    payload = { 'api_key': 'ab75344fcf729c63c9665e8e8a21d985', 'url': url}
        r = requests.get('https://api.scraperapi.com/', params=payload,timeout=120)
        return {'status': r.status_code, 'body': r.text}
    #    
    def create_brand_search_query(self, sku):
        #query = f"\"{sku}\""
        return f"https://www.google.com/search?q={sku}"

    @staticmethod
    def parse_google_results(html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        results = []
        for g in soup.find_all('div', class_='g'):
            links = g.find_all('a')
            if links and 'href' in links[0].attrs:  # check if 'href' attribute exists
                results.append(links[0]['href'])
        return results
    
class FilterUrls:
    def __init__(self,list_url,brand):
        
        self.whitelisted_domains = [
        "fwrd.com",
        "modesens.com",
        "saksfifthavenue.com",
        "saksoff5th.com",
        "nordstrom.com",
        "nordstromrack.com"
    ]   
        self.brand_settings = BrandSettings(json.loads(open(BRANDSETTINGSPATH,encoding='utf-8').read()))
        self.settings_for_brand = self.brand_settings.get_rules_for_brand(brand)
        self.url_list_nodups = self.remove_duplicates(list_url)
        self.filtered_urls = self.filter_urls_by_brand_and_whitelist(self.url_list_nodups, self.settings_for_brand, self.whitelisted_domains)
        
    def filter_urls_helper(self):   
        
        if self.filtered_urls:
            print("1_filter",self.filtered_urls,"+X+")
            self.filtered_urls = self.filter_urls_by_currency(['/us/','/us/en/','/en-us/','/us-en/','/us.','modesens.com/product','fwrd.com/mobile/product','marcjacobs.com/default/'], self.filtered_urls)
            print("2_filter",self.filtered_urls)
            
            
            
            
    def remove_duplicates(self,input_list):
        """
        Remove duplicates from a list while preserving the order of the original list.

        Args:
            input_list (list): The input list with potential duplicates.

        Returns:
            list: A new list with duplicates removed.
        """
        seen = set()  # Initialize an empty set to store seen elements
        result = []   # Initialize an empty list to store unique elements in order

        for item in input_list:
            if item not in seen:
                seen.add(item)  # Add the item to the set if it's not seen before
                result.append(item)  # Add the item to the result list

        return result

    def filter_urls_by_brand_and_whitelist(self, urls, brand_settings, whitelisted_domains):
        brand_domains = [domain.replace('www.', '') for domain in brand_settings.get("domain_hierarchy", [])]
        whitelisted_domains = [domain.replace('www.', '') for domain in whitelisted_domains]
        approved_brand_urls = []
        approved_whitelist_urls = []

        if isinstance(urls, str):
            urls = urls.split(',')

        for url in urls:
            url = str(url).strip()
            if not url.startswith(('http://', 'https://')):
                url = 'http://' + url

            try:
                parsed_url = urlparse(url)
                domain = parsed_url.netloc
                if domain.startswith('www.'):
                    domain = domain[4:]

                if domain in brand_domains:
                    approved_brand_urls.append([url, "brand"])
                elif domain in whitelisted_domains:
                    approved_whitelist_urls.append([url, "whitelist"])

            except Exception as e:
                print(f"Error parsing URL '{url}': {e}")
        
        # Combine brand URLs and whitelisted URLs
        approved_urls = approved_brand_urls + approved_whitelist_urls
        return approved_urls if approved_urls else None
################################
    def filter_urls_by_currency(self, currency_items, urls):
        print(f'Filtering URLs by currency: {currency_items}')
        filtered_urls = []
        print(f'Filtered {urls}')
        for url in urls:
            print("------")
            print(url)
            print(f"url: {url}")
            for item in currency_items:
                #print(f'item: {item} url: {url}')
                #print(f'item: {type(item)} url: {type(url)}')
                #print(url)
                if str(item.lower()) in str(url[0]).lower():
                    print(f"item: {item} url: {url}")
                    filtered_urls.append(url)
                    break
        print(f'FilteredXXXURLs: {filtered_urls}')    
        return filtered_urls
    
class DataFetcher:
    def __init__(self,url,brand):
        self.brand_settings = BrandSettings(json.loads(open(BRANDSETTINGSPATH,encoding='utf-8').read())).get_rules_for_brand(brand)
        self.url = url['url']
        self.modesens = None
        self.url_type = url['type']
        self.raw_html = self.send_regular_request(self.url)
        print(self.raw_html['status'],"+X")
        if self.raw_html['status'] == 200:
       
            self.product_schemas = self.extract_product_schema(self.raw_html['body'])
            print(self.product_schemas,"+-+")
            ####! GUCCI PRODUCT RETURNING RESULTS 760246 10O0Y 5701
          
            if self.product_schemas:
                
                
                self.parsed_products = self.parse_product_schemas(self.product_schemas)
                ##!!! GUCCI RETURNING SELLER AS NONE
                print(self.parsed_products,"+--+")
                if self.parsed_products:
                    self.parsed_products=self.seller_verification(self.parsed_products,self.url_type)
                    print(self.parsed_products,"++XX+")
                else:
                    self.parsed_products = None
                
                
                print(type(self.parsed_products),self.parsed_products,"+++")    
                if "modesens" in self.url and self.parsed_products is not None:
                    self.modesens=ModesensParser(self.raw_html['body'],self.brand_settings)
                    if self.modesens.verify_seller:
                        self.parsed_products['prices'] = self.modesens.verify_seller["price"]
                        self.parsed_products['currency'] = self.modesens.verify_seller["currency"]
                        self.parsed_products['seller'] = self.modesens.verify_seller["seller"]
                    else:
                        self.parsed_products = None             
            else:
                self.parsed_products = None

        else:
            self.parsed_products = None        
            
    def seller_verification(self,product_details,url_type):
        approved_seller_list = [
         'saks fifth avenue',
         'nordstrom',
         'fwrd',
         'forward',
         'modesens',
         'ssense',
         'net-a-porter',
         'luisaviaroma',
         'burberry united states'
        ]
        for index,product in enumerate(product_details):
            if url_type == "brand" and product['prices'] is not None:
                return product_details[index]
            if product['seller'] is not None:
                if (product['seller'].lower() in approved_seller_list) or (product['seller'].lower() in list(map(lambda x:x.lower(),self.brand_settings['names']))):     
                    return product_details[index]
                else:
                    continue
            else:
                continue
        return None       
        
    def send_regular_request(self, url):
        payload = { 'api_key': 'ab75344fcf729c63c9665e8e8a21d985', 'url': url, 'country_code': 'us'}
#        payload = { 'api_key': 'ab75344fcf729c63c9665e8e8a21d985', 'url': url}
        r = requests.get('https://api.scraperapi.com/', params=payload ,timeout=120)
        return {'status': r.status_code, 'body': r.text}

    def extract_product_schema(self, html_content):
        product_schemas = []  # List to store all found product schemas

        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            schema_tags = soup.find_all('script', {'type': 'application/ld+json'})

            for tag in schema_tags:
                try:
                    data = json.loads(tag.text)
                    if data.get('@type') == 'Product':
                        # Log the raw product schema for debugging
                        logging.debug("Raw Product Schema: %s", json.dumps(data, indent=4))
                        product_schemas.append(data)
                except json.JSONDecodeError:
                    continue

            if not product_schemas:
                logging.warning("No Product schema found in the HTML content.")
                return None

            return product_schemas
        except Exception as e:
            logging.error(f"Error extracting product schemas from HTML: {e}")
            return None

                
    def get_parsed_products(self):
        return self.parsed_products

    def parse_product_schemas(self,product_schemas):
        parsed_products = []

        for schema in product_schemas:
            if schema.get('@type') == 'Product':
                offers_info = self.extract_offers(schema)
                for offer in offers_info:
                    
                    if(offer.get('@type') == 'Offer'):
                        prices=self.get_prices(offer)
                        currency=self.get_currency(offer)
                        seller=self.get_seller(offer)
                        description=self.get_description(offer)
                        title=self.get_title(offer)
                        images=self.get_images(offer)
                        url=self.get_url(offer)
                        product_details = self.create_product_details(title,images,prices,currency,url,description,seller,schema)
                        parsed_products.append(product_details)
                        
                    elif(offer.get('@type') == 'AggregateOffer'):
                        for suboffer in self.extract_offers(offer):
                            prices=self.get_prices(suboffer)
                            currency=self.get_currency(suboffer)
                            seller=self.get_seller(suboffer)
                            description=self.get_description(suboffer)
                            title=self.get_title(suboffer)
                            images=self.get_images(suboffer)
                            url=self.get_url(suboffer)
                            product_details = self.create_product_details(title,images,prices,currency,url,description,seller,schema)
                            parsed_products.append(product_details)
        return parsed_products



    def get_title(self, data):
        if isinstance(data, dict):
            for key, value in data.items():
                if key.lower() not in ['seller','brand']:
                    if key == 'name':
                        return value
                    else:
                        result = self.get_title(value)
                        if result:
                            return result
        else: return None        
            
    def get_images(self,data):
        images = []
        if isinstance(data, dict):
            for key, value in data.items():
                if key == 'image' and isinstance(value, (list, str)):
                    if isinstance(value, list):
                        images.extend(value)
                    else:
                        images.append(value)
                else:
                    images.extend(self.get_images(value))
        elif isinstance(data, list):
            for item in data:
                images.extend(self.get_images(item))
        return images

    def get_prices(self,data):
        prices = []
        if isinstance(data, dict):
            for key, value in data.items():
                if key.lower() in ['price', 'lowprice', 'highprice'] and isinstance(value, str):
                    prices.append(value.replace("$", "").replace(",", "").replace(" ", ""))
                elif key.lower() in ['price', 'lowprice', 'highprice'] and isinstance(value, (int, float)):
                    prices.append(value)
                else:
                    prices.extend(self.get_prices(value))
        elif isinstance(data, list):
            for item in data:
                prices.extend(self.get_prices(item))
        return prices 

    def get_currency(self,data):
        if isinstance(data, dict):
            currency = data.get('priceCurrency', None)
            if currency:
                return currency
            for value in data.values():
                result = self.get_currency(value)
                if result:
                    return result
        elif isinstance(data, list):
            for item in data:
                result = self.get_currency(item)
                if result:
                    return result
    def get_url(self,data):
        if "modesens" in self.url:
            if isinstance(data, dict):
                url = data.get('url', None)
                if url:
                    return f"https://modesens.com{url}"
                for value in data.values():
                    result = self.get_url(value)
                    if result:
                        return f"https://modesens.com{url}"
            elif isinstance(data, list):
                for item in data:
                    result = self.get_url(item)
                    if result:
                        return f"https://modesens.com{url}"
        else:
            if isinstance(data, dict):
                url = data.get('url', None)
                if url:
                    return f"{url}"
                for value in data.values():
                    result = self.get_url(value)
                    if result:
                        return f"{url}"
            elif isinstance(data, list):
                for item in data:
                    result = self.get_url(item)
                    if result:
                        return f"{url}"
        
                
                
    def get_description(self,data):
        if isinstance(data, dict):
            for key, value in data.items():
                if key == 'description':
                    return value
                else:
                    result = self.get_description(value)
                    if result:
                        return result
                    
    def get_seller(self,data):
        if isinstance(data, dict):
            seller = data.get('seller', None)
            if isinstance(seller, dict) and 'name' in seller:
                return seller['name']
            for value in data.values():
                result = self.get_seller(value)
                if result:
                    return result
        elif isinstance(data, list):
            for item in data:
                result = self.get_seller(item)
                if result:
                    return result


    def extract_offers(self,data):
        offers = []

        if isinstance(data, dict):
            if 'offers' in data:
                # Directly append the offer or aggregate offer object
                offer_data = data['offers']
                if isinstance(offer_data, list):
                    offers.extend(offer_data)  # List of individual offers
                else:
                    offers.append(offer_data)  # Single or aggregate offer
            else:
                # Recursively search for offers in other dictionary values
                for value in data.values():
                    offers.extend(self.extract_offers(value))

        elif isinstance(data, list):
            # If the data is a list, apply the function to each element
            for item in data:
                offers.extend(self.extract_offers(item))

        return offers

    def create_product_details(self, title,images,prices,currency,url,description,seller,schema):
        product_details = {
                        'title': title,  
                        'images': images,  
                        'prices': prices,
                        'currency': currency,
                        'url': url,  
                        'description': description,  
                        'seller': seller.lower() if seller else None
                    }
        for key, value in product_details.items():
            if value in [None,[],"",{}]:
                if key == 'title':
                    product_details[key] = self.get_title(schema)
                elif key == 'images':
                    product_details[key] = self.get_images(schema)
                elif key == 'prices':
                    product_details[key] = self.get_prices(schema)
                elif key == 'currency':
                    product_details[key] = self.get_currency(schema)
                elif key == 'url':
                    product_details[key] = self.get_url(schema)
                elif key == 'description':
                    product_details[key] = self.get_description(schema)
                elif key == 'seller':
                    seller = self.get_seller(schema)
                    product_details[key] = seller.lower() if seller else seller
        return product_details
    
    def is_seller_verified(self, brand, seller):
        brand = brand.lower()
        seller = seller.lower()
        print('brand: {brand} seller: {seller}')
        return brand in seller or seller in brand
    
    def select_details(self, parsed_products, brand_settings):
        selected_product = None
        for product in parsed_products:
            if self.is_seller_verified(brand_settings['names'][0], product['seller']):
                selected_product = product
                break
        return selected_product
    
class ModesensParser():
    def __init__(self, html,brand_settings):
        self.brand_settings = brand_settings
        self.soup=BeautifulSoup(html, 'html.parser')
        self.blocks=self.extract_blocks()
        self.product_details=self.get_product_details()
        self.verify_seller = self.seller_verification(self.product_details)
    
    def extract_blocks(self):
        blocks = self.soup.find_all('div', class_='d-inline-block each-list-con')
        return blocks
    def seller_verification(self,product_details):
        approved_seller_list = [
         'saks fifth avenue',
         'nordstrom',
         'fwrd',
         'forward',
         'modesens',
         'ssense',
         'net-a-porter'
        ]
        for index,product in enumerate(product_details):
            if product['seller'] is not None:
                if (product['seller'].lower() in approved_seller_list) or (product['seller'].lower() in list(map(lambda x:x.lower(),self.brand_settings['names']))):     
                    return product_details[index]
                else:
                    continue
            else:
                continue
        return None
        
         
    def get_product_details(self):
        product_details = [] 

        for block in self.blocks:
            # Handle different types of price blocks
            product_detail={}
            price_box = block.find('div', class_='price-box') or block.find('span', class_='price-box')
            merchant_name = block.find('div', class_='merchant-name')
            
            # Extracting seller
            seller = merchant_name.get_text(strip=True) if merchant_name else None
            prices = []
            if price_box:
                # Find all span elements that potentially contain prices
                price_spans = price_box.find_all('span', class_='position-relative') or [price_box]
                for span in price_spans:
                    # Extracting numeric part of the price
                    price_text = span.get_text(strip=True)
                    match = re.search(r'\d+(?:\.\d+)?', price_text)
                    
                    if match:
                        price = float(match.group())
                        prices.append(price)

                    # Extracting currency symbol
                    currency = price_text[0] if price_text else None

            # Store the highest price, seller, and currency
            if prices:
                highest_price = max(prices)
                product_detail['price']=highest_price
                product_detail['seller']=seller
                product_detail['currency']=currency
                product_details.append(product_detail)

        return product_details
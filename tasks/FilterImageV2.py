import re
import json
import requests
from urllib.parse import urlparse

class FilterUrlsV2:
    def __init__(self, url_dicts, brand, sku):
        self.brand = brand.lower()
        self.sku = sku.lower()
        self.url_dicts_nodups = self.remove_dups(url_dicts)

        # URLs for JSON files containing filtering rules
        self.json_url_2 = "https://raw.githubusercontent.com/nikiconluxury/images-filter/main/step_2_filter_images.json"
        self.brand_settings_url = 'https://raw.githubusercontent.com/nikiconluxury/images-filter/main/brand_settings.json'

        # Fetch JSON data from the URLs
        self.json_dict_2 = self.fetch_json_from_url(self.json_url_2)
        self.brand_settings = self.fetch_json_from_url(self.brand_settings_url)

        self.filtered_result = self.filter_image_dict(self.url_dicts_nodups)

    def clean_string(self, input_string):
        # Check if input string is None, return empty string if so
        if input_string is None:
            return ""
        # Remove non-alphanumeric characters except spaces using regex
        cleaned = re.sub(r'[^a-zA-Z0-9 ]+', '', input_string)
        # Replace multiple spaces with a single space
        cleaned = ' '.join(cleaned.split())
        # Convert to lowercase and strip whitespace from the ends
        cleaned = cleaned.lower().strip()
        cleaned = cleaned.replace(" ", "")
        return cleaned

    def fetch_json_from_url(self, url):
        try:
            # Send a GET request to the URL
            response = requests.get(url)
            # Raise an exception for 4xx and 5xx status codes
            response.raise_for_status()
            # Parse the response as JSON
            json_data = response.json()
            return json_data
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            # Handle any errors that occur during the request or JSON parsing
            print(f"Error fetching JSON from URL: {e}")
            return None

    def remove_duplicates(self, lst):
        # Create an empty set to store unique items
        seen = set()
        # Create a new list to store the result
        new_lst = []
        # Iterate over each item in the input list
        for item in lst:
            # Check if the item is not None and hasn't been seen before
            if item is not None and item not in seen:
                # Add the item to the new list and mark it as seen
                new_lst.append(item)
                seen.add(item)
        return new_lst

    def get_domain(self, url):
        # Check if the URL is None, return empty string if so
        if url is None:
            return ""
        # Parse the URL using urlparse
        parsed_url = urlparse(url)
        # Extract the domain from the parsed URL
        domain = parsed_url.netloc
        return domain

    def filter_image_dict(self, image_urls_dict):
        # Check if JSON data was fetched successfully
        if self.json_dict_2 is None:
            return "Error fetching JSON data"

        # List to store image dictionaries that pass the filtering criteria
        second_pass = []
        # Iterate over each image dictionary in the input list
        for image_dict in image_urls_dict:
            # Check if the image dictionary is not None
            if image_dict:
                # Extract relevant fields from the image dictionary
                url = image_dict.get("url", "")
                description = image_dict.get("description", "")
                sku = image_dict.get("sku", "")
                brand = image_dict.get("brand", "")
                # Check if the image passes the filtering criteria using get_score_2
                score = self.get_score_2(url, description, sku, brand, self.json_dict_2)
                if score:
                    image_dict['score'] = score
                    second_pass.append(image_dict)
            else:
                print('encountered none object in image_urls_dict')
                print(image_urls_dict)

        # Check if any images passed the filtering criteria
        if not second_pass:
            return 'None found in this filter'
        else:
            # Return the image dictionary with the highest score
            return max(second_pass, key=lambda x: x['score'])
    def get_score_2(self, url, description, sku, brand, point_dict):
        # Segment the SKU into possible article, model, and color combinations
        sku = sku.replace(brand,"")
        possible_amc = self.segment_workflow(sku, brand)

        # If no possible combinations found, return False
        if not possible_amc:
            return False

        # Get brand names and remove duplicates
        brand_names = self.get_brand_names(brand)
        brand_names = self.remove_duplicates([self.clean_string(name) for name in brand_names])

        # Get score values from the point dictionary
        article_model_score_value = point_dict.get("article", 0)
        color_score_value = point_dict.get("color", 0)
        brand_score_value = point_dict.get("brand", 0)
        threshold = point_dict.get("threshold", 0)
        print(f"Article Model Score Value: {article_model_score_value}, Color Score Value: {color_score_value}, Brand Score Value: {brand_score_value}, Threshold: {threshold}")
        # Clean the URL and description strings
        url = self.clean_string(url)
        description = self.clean_string(description)

        fullsku = possible_amc[0].get('full_sku', None)
        if fullsku:
            print(f'Using Full Sku {fullsku} Brand {brand_names}')
            for amc_dict in possible_amc:
                current_score = 0
                for value in amc_dict.values():
                    print("value ", value)
                    value = self.clean_string(value)
                    if value in url:
                        print(f"Got a point for {value} in url {url}")
                        current_score += 1
                    if value in description:
                        print(f"Got a point for {value} in description {description}")
                        current_score += 1
                for brand in brand_names:
                    brand = self.clean_string(brand)
                    print(brand)
                    print(f"Url: {url} Description {description}")
                    if brand in url:
                        print(f"Got a point for {brand}")
                        current_score += brand_score_value
                    elif brand in description:
                        print(f"Got a point for {brand}")
                        current_score += brand_score_value

                if current_score >= threshold:
                    print(f'Using Full Sku {fullsku} Brand {brand_names} Current Score {current_score}')
                    return current_score
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

                if current_score >= threshold:
                    return current_score

        # If no combination meets the threshold, return False
        return 0

    def filter_urls(self, url_dicts):
        filtered_url_dicts = []
        # Iterate over each URL dictionary
        for url_dict in url_dicts:
            # Get the URL from the dictionary, strip whitespace, and add 'http://' if missing
            url = url_dict.get('url', '').strip()
            if not url.startswith(('http://', 'https://')):
                url = 'http://' + url

            # Get the domain from the URL and convert to lowercase
            domain = self.get_domain(url).lower()
            # Remove 'www.' from the domain if present
            if domain.startswith('www.'):
                domain = domain[4:]

            # Initialize the reason for including the URL as None
            reason = None
            # Check if the domain matches any whitelisted domain or its subdomain
            domain_matched = any(domain == wl_domain or domain.endswith('.' + wl_domain)
                                 for wl_domain in self.whitelisted_domains)

            # Check if the SKU is present in the URL (case-insensitive)
            if self.sku in url.lower():
                reason = "sku"
            # Check if the brand is present in the URL (case-insensitive)
            elif self.brand in url.lower():
                reason = "brand"
            # Check if the domain is whitelisted
            elif domain_matched:
                reason = "whitelist"

            # If a reason for inclusion is found, add the URL dictionary to the filtered list
            if reason:
                modified_url_dict = url_dict.copy()
                modified_url_dict['type'] = reason
                filtered_url_dicts.append(modified_url_dict)

        return filtered_url_dicts

    def remove_dups(self, url_dicts):
        seen = set()
        new_list = []
        # Iterate over each URL dictionary
        for url_dict in url_dicts:
            # Check if the URL is not already seen
            if url_dict.get('url') not in seen:
                # Add the URL to the set of seen URLs
                seen.add(url_dict['url'])
                # Add the URL dictionary to the new list
                new_list.append(url_dict)
        return new_list

    def segment_workflow(self, sku, brand):
        # Segment the SKU into potential segments
        segments = self.segment_sku(sku, brand)
        # If no segments found, return an empty list
        if not segments or len(segments) < 3:
            return [{'full_sku': str(sku.replace(brand, ""))}]

        # Generate sublists of the segments
        sublists_list = list(self.sublists(segments))
        # Clean the sublists by combining segments
        result = self.clean_sublist(sublists_list)
        # Filter the sublists based on length criteria
        filtered_result = self.filter_sublists_by_length(result)
        # Transform the filtered sublists into dictionaries
        final_result = self.transform_sublist(filtered_result)
        return final_result

    def get_rules_for_brand(self, brand_name):
        # Convert brand_name to lowercase for case-insensitive comparison
        brand_name_lower = brand_name.lower()
        for rule in self.brand_settings.get('brand_rules', []):
            # Convert each name in rule['names'] to lowercase and check if brand_name_lower is among them
            if brand_name_lower in [name.lower() for name in rule['names']]:
                return rule
        return None

    def get_brand_names(self, brand):
        return self.get_brand_img_names(brand)

    def get_brand_img_names(self, brand_name):
        # Convert brand_name to lowercase for case-insensitive comparison
        brand_rules = self.get_rules_for_brand(brand_name)
        if brand_rules:
            return brand_rules.get('names', [])
        else:
            return [brand_name]

# Unused functions separated below

    def segment_sku(self, sku, brand):
        # Clean the SKU string and remove the brand name
        sku = self.clean_string(sku).replace(brand, "")
        # Get the indices of non-alphanumeric characters in the SKU
        indices = self.get_indices(sku)
        # If there are less than 2 non-alphanumeric characters, return the SKU as a single segment
        if len(indices) < 2:
            return [sku]
        # Split the SKU string at the non-alphanumeric indices
        segments = self.split_string_at_indices(sku, indices)
        # Return only non-empty segments
        return [segment for segment in segments if segment]

    def get_indices(self, s):
        # Return the indices of non-alphanumeric characters in the string
        return [i for i, char in enumerate(s) if not char.isalnum()]

    def split_string_at_indices(self, s, indices):
        start = 0
        segments = []
        # Split the string at each index and add the substring to the segments list
        for index in indices:
            segments.append(s[start:index])
            start = index + 1
        segments.append(s[start:])
        return segments

    def sublists(self, lst):
        # Generate all possible sublists of the input list
        return [[lst[i:j] for i, j in zip([0] + list(combo), list(combo) + [len(lst)])]
                for combo in self.combinations(range(1, len(lst)))]

    def combinations(self, iterable):
        # Generate all possible combinations of the input iterable
        return (combination for length in range(len(iterable) + 1)
                for combination in self.combinations_helper(iterable, length))

    def combinations_helper(self, iterable, length):
        # Helper function to generate combinations recursively
        if length == 0:
            yield []
        elif length == 1:
            for item in iterable:
                yield [item]
        else:
            for i, item in enumerate(iterable):
                for combo in self.combinations_helper(iterable[i + 1:], length - 1):
                    yield [item] + combo

    def clean_sublist(self, sublists):
        processed_sublists = []
        # Clean each sublist by combining its inner lists
        for s_list in sublists:
            if len(s_list) == 3:
                new_sublist = []
                for inner_list in s_list:
                    combined_string = ''.join(inner_list)
                    new_sublist.append([combined_string])
                processed_sublists.append(new_sublist)
        return processed_sublists

    def filter_sublists_by_length(self, result):
        # Filter sublists based on length criteria
        return [sublist for sublist in result
                if len(''.join(sublist[0])) >= 3 and len(''.join(sublist[1])) >= 3]

    def transform_sublist(self, input_list):
        # Transform the input list into a list of dictionaries
        return [{"article": item[0][0], "model": item[1][0], "color": item[2][0]} for item in input_list]
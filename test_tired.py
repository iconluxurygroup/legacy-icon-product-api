from typing import Dict

def fetch_and_parse_html(classified_url: Dict[str, str],brand_name: str):
    print(type(classified_url))
fetch_and_parse_html({'url': 'https://www.amazon.com/dp/B07H8Q3JH1', 'type': 'product', 'variation': 'variation'},'brand_name')
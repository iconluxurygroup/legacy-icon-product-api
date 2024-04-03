from tasks.LR import LR
import re, ast,unicodedata,json


def get_original_images(soup):
    start_tag = 'FINANCE",[22,1]]]]]'
    end_tag = '":[null,null,null,1,['
    #matched_google_image_data = re.findall(r'FINANCE",[22,1]]]]]\\":\[1\](.+?)CP2oB0', str(soup))
    matched_google_image_data = LR().get(soup, start_tag,end_tag)
    print(matched_google_image_data)
    print(type(matched_google_image_data))

    thumbnails = [
        bytes(bytes(thumbnail, 'utf-8').decode("unicode-escape"), "utf-8").decode("unicode-escape") for thumbnail in matched_google_image_data
    ]
    #print(thumbnails)
    
    matched_google_images_thumbnails = ", ".join(
        re.findall(r'\[\"(https\:\/\/encrypted-tbn0\.gstatic\.com\/images\?.*?)\",\d+,\d+\]',
                   str(thumbnails))).split(", ")
    
    #print(matched_google_images_thumbnails)
    matched_description = re.findall(r'"2003":\[null,"[^"]*","[^"]*","(.*?)"', str(thumbnails))
    # Extract full resolution images
    #matched_google_full_resolution_images = re.findall(r"(?:|,),\[\"(https:|http.*?)\",\d+,\d+\]", str(thumbnails))

    removed_matched_google_images_thumbnails = re.sub(
    r'\[\"(https\:\/\/encrypted-tbn0\.gstatic\.com\/images\?.*?)\",\d+,\d+\]', "", str(thumbnails))

    # Extract full resolution images
    matched_google_full_resolution_images = re.findall(r"(?:|,),\[\"(https:|http.*?)\",\d+,\d+\]", removed_matched_google_images_thumbnails)
    

    print(len(matched_description))
    

    full_res_images = [
        bytes(bytes(img, "utf-8").decode("unicode-escape"), "utf-8").decode("unicode-escape") for img in matched_google_full_resolution_images
        ]
    cleaned_urls = [clean_image_url(url) for url in full_res_images]
    #print(len(cleaned_descriptions))
    #print(matched_description)
    # Assume descriptions are extracted
    #descriptions = LR().get(soup, '"2008":[null,"', '"]}],null,') # Replace 'description_pattern' with your actual regex pattern for descriptions

    final_thumbnails = []
    final_full_res_images = []
    final_descriptions = []
    print(type(matched_description))
    if len(cleaned_urls) > 10:
        cleaned_urls = cleaned_urls[:10]
        final_descriptions = matched_description[:10]

    return cleaned_urls,final_descriptions


def clean_image_url(url):
    # Pattern matches common image file extensions followed by a question mark and any characters after it
    pattern = re.compile(r'(.*\.(?:png|jpg|jpeg|gif))(?:\?.*)?', re.IGNORECASE)

    # Search for matches in the input URL
    match = pattern.match(url)

    # If a match is found, return the part of the URL before the query parameters (group 1)
    if match:
        return match.group(1)

    # If no match is found, return the original URL
    return url


# with open("text.html", "r", encoding='utf-8') as f:
#     html_content = f.read()
#     results = get_original_images(html_content)
#     print(results)
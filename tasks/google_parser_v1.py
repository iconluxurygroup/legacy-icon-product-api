from tasks.LR import LR
import re, ast,unicodedata

# Start and end tags used in HTML processing
line_start_tag = '[[{"444383007":[1,[0,'
line_end_tag = ']}]]'

def d_instance(input_string, delimiter=",", instance=8):
    # Split the input string and truncate it after the specified instance
    split_list = input_string.split(delimiter)
    cut_off_list = split_list[:instance] if len(split_list) > instance else split_list

    # Reassemble the truncated list into a string
    result_string = delimiter.join(cut_off_list)

    # Attempt to correct improper string endings
    try:
        eval(result_string)
    except SyntaxError:
        result_string = fix_string_by_replacing_quotes(result_string)

    return result_string

def decode_html_content(html):
    if isinstance(html, bytes):
        # Decode byte sequences, with a fallback to ISO-8859-1 for common web encoding issues
        try:
            return html.decode('utf-8')
        except UnicodeDecodeError:
            return html.decode('iso-8859-1')
    elif isinstance(html, str):
                # Handle strings with encoded byte sequences
        try:
            html_as_bytes = bytes(html, "utf-8").decode("unicode_escape").encode("latin1")
            return html_as_bytes.decode("utf-8")
        except:
            return html  # Return the original string if decoding fails
        else:
            raise ValueError("Unsupported type for HTML content.")

def fix_string_by_replacing_quotes(input_string):
    return input_string.replace('\\"', "'")
def trim_lists_to_same_length(*lists): 
    if not lists:
        return tuple()
    
    # Find the minimum length among all lists
    min_length = min(len(lst) for lst in lists)
    
    # Trim lists to the minimum length by slicing
    trimmed_lists = [lst[:min_length] for lst in lists]
    
    return tuple(trimmed_lists)
def get_original_images(html):
    image_links_list = []
    descrip_list = []

    html = decode_html_content(html)
    grid = LR().get(html, '["GRID_STATE0"', 'stopScanForCss')
    if grid:
        print("Get Grid!")
    # Pattern to match text within specified start and end tags
    pattern = re.escape(line_start_tag) + '(.*?)' + re.escape(line_end_tag)
    matches = re.findall(pattern, str(grid), re.DOTALL)
    if not matches:
        return False
    print(len(matches))
    for match in matches:
        list_img, list_desc = extract_image_and_description(match)
        image_links_list.append(list_img[0])
        # Check if list_desc is an instance of list
        if isinstance(list_desc, list):
            # Check if index 3 exists in the list
            if len(list_desc) > 3:
                # Take the element at index 3 and append it
                descrip_list.append(list_desc[3])
            else:
                # If index 3 doesn't exist, just append the whole list (if this is your intended behavior)
                print(f"Debug: {list_desc}")
                #raise
                #descrip_list.extend(list_desc)
        else:
            # If list_desc is not a list, print it for debugging
            print(f"Debug Not Exist: {list_desc}")
    print(f"{len(image_links_list)}\n{len(descrip_list)}")



    image_links_list,descrip_list = trim_lists_to_same_length(image_links_list,descrip_list)
    if not image_links_list or not descrip_list:
        raise ValueError(f"Either 'urls' or 'descriptions' list is empty.\n{image_links_list}\n{descrip_list}\n")
    image_links_list = clean_strings(image_links_list)
    descrip_list = clean_strings(descrip_list)
    return image_links_list,descrip_list

def extract_image_and_description(match):
    list_pattern = r"(\[.*?\])"
    list_matches = re.findall(list_pattern, str(match))
    try:
        list_img = ast.literal_eval(list_matches[1])
    except SyntaxError:
        if list_matches[1].count('"') % 2 != 0:  # Odd number of double quotes
            print()
            list_matches[1] += '"'  # Attempt to close the string
        elif list_matches[1].count("'") % 2 != 0:  # Odd number of single quotes
            list_matches[1] += "'"  # Attempt to close the string
        list_img = ast.literal_eval(list_matches[1])

        
    print(f"Debug : {list_matches[3]}\n\n-----\n{list_matches}")
    list_desc = process_description(list_matches[3])
    if not list_img or not list_desc:
        print(f"Either 'urls' or 'descriptions' list is empty.\n{list_img}\n{list_matches}")
    return list_img, list_desc
def clean_strings(strings):
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
                cleaned = cleaned.replace('\u003d','=')
                print(f"Cleaned...{cleaned}")
                cleaned_strings.append(cleaned)
            except Exception as e:
                # Log or handle any exceptions raised during the process
                print(f"Error cleaning string {s}: {e}")
                # Add the original string if there was an error
                cleaned_strings.append(s)
        return cleaned_strings
def process_description(description):
    description = description.replace(',{"26":[null,2]',']')
    description = description.replace('null','"None"').replace(',true',',"True"').replace('false','"False"')
    #description = clean_strings(description)
    try:
        print(description)
        cleaned = unicodedata.normalize('NFKC', description)
        cleaned = cleaned.replace('\u003d','=')
        print(cleaned)
        list_elements = ast.literal_eval(cleaned)
    except SyntaxError:
    # Check if the description ends with a double quote
        print(f"DESCRIPTION: {description}")
        description = str(d_instance(description)) 
        if description.endswith('"'):
            description += ']'
        else:
            description += '"]'
        print(f"DESCRIPTION: {description}")
        list_elements = ast.literal_eval(description)
        print("----------------------------\n")
        print(list_elements)

    return list_elements


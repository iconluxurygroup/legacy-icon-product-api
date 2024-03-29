from tasks.LR import LR
import re, ast

# Start and end tags used in HTML processing
line_start_tag = '[[{"444383007":[1,[0,'
line_end_tag = ']}]]'

def d_instance(input_string, delimiter=",", instance=8):
    """
    This function processes a string representation of a list by splitting it at a specified delimiter
    and truncates it after a given instance, then returns the modified list as a string.

    :param input_string: String representation of the list to process.
    :param delimiter: Delimiter for splitting the string. Defaults to ",".
    :param instance: Instance after which the list is cut off. Defaults to 6.
    :return: Modified string representation of the list.
    """
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
    """
    Decodes HTML content, handling both byte sequences and strings with possible encoding issues.

    :param html: HTML content to decode.
    :return: Decoded HTML content as a string.
    """
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
    """
    Replaces escaped double quotes with single quotes in a string.

    :param input_string: The string to process.
    :return: The string with escaped double quotes replaced.
    """
    return input_string.replace('\\"', "'")
def trim_lists_to_same_length(*lists):
    """
    Trims given lists so they all have the same length, by removing elements
    from the end of longer lists. If no lists are given or if all lists are
    already of the same length, no trimming is done.
    
    Parameters:
    - lists: Variable number of list arguments
    
    Returns:
    - A tuple of lists, all trimmed to the same length.
    """
    
    if not lists:
        return tuple()
    
    # Find the minimum length among all lists
    min_length = min(len(lst) for lst in lists)
    
    # Trim lists to the minimum length by slicing
    trimmed_lists = [lst[:min_length] for lst in lists]
    
    return tuple(trimmed_lists)
def get_original_images(html):
    #print(html)
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
        print(f"Either 'urls' or 'descriptions' list is empty.\n{image_links_list}\n{descrip_list}\n")
    return image_links_list,descrip_list

def extract_image_and_description(match):
    """
    Extracts image URLs and descriptions from a match string.

    :param match: The matched string containing image and description data.
    :return: A tuple containing the list of image URLs and the list of descriptions.
    """
    list_pattern = r"(\[.*?\])"
    list_matches = re.findall(list_pattern, str(match))

    # Process image URL and description lists

    try:
        list_img = ast.literal_eval(list_matches[1])
    except SyntaxError:
        if list_matches[1].count('"') % 2 != 0:  # Odd number of double quotes
            print()
            list_matches[1] += '"'  # Attempt to close the string
        elif list_matches[1].count("'") % 2 != 0:  # Odd number of single quotes
            list_matches[1] += "'"  # Attempt to close the string
        list_img = ast.literal_eval(list_matches[1])
    #except Exception as e:
        #print(e)
        #raise 
        
    print(f"Debug : {list_matches[3]}\n\n-----\n{list_matches}")
    list_desc = process_description(list_matches[3])
    if not list_img or not list_desc:
        print(f"Either 'urls' or 'descriptions' list is empty.\n{list_img}\n{list_matches}")
    return list_img, list_desc

def process_description(description):
    """
    Processes a string containing image descriptions to correct format errors and convert to a list.

    :param description: String containing the image descriptions.
    :return: Processed list of descriptions.
    """
    description = description.replace(',{"26":[null,2]',']')
    description = description.replace('null','"None"').replace(',true',',"True"').replace('false','"False"')

    try:
        list_elements = ast.literal_eval(description)
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


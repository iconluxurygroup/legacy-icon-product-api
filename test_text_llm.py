import requests

API_URL = "https://api-inference.huggingface.co/models/google/gemma-7b-it"
headers = {"Authorization": "Bearer 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"}

def query(payload):
	response = requests.post(API_URL, headers=headers, json=payload)
	return response.json()



# Define your variables
vision_image_desc = "a black bag with a sticker on it and a strap"
image_title = "ょゆァ-FD55SA258L40 99 Men's Crossbody | TRENBE"
brand = "Kenzo"
context = "Accessory"

# Combine the image description and title for a more detailed prompt
prompt = f"Given the description '{vision_image_desc}' and the title '{image_title}', is this a correct match for the brand '{brand}' and the context '{context}'? Return 'True' for a correct match and 'False' for an incorrect match."

# Example function call (ensure to replace `query` with your actual function or method for querying the LLM)
output = query({
    "inputs": prompt
})

print(output)

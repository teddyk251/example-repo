# ocr.py
# Calls the OCR endpoint to extract fields from an image or PDF file.

import requests
import time
import os

OCR_URL = os.getenv("OCR_URL")

def extract_fields_from_image(image_path):
    """
    Sends an image or PDF to the FastAPI OCR endpoint and gets the extracted fields.
    
    Args:
        image_path (str): Path to the image or PDF file to be processed.
    
    Returns:
        dict: The extracted fields as a JSON response.
    """
    url = f"{OCR_URL}/extract"

    # Start timing
    start_time = time.time()

    with open(image_path, 'rb') as image_file:
        files = {'file': image_file}
        response = requests.post(url, files=files)

        # End timing
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Time taken: {elapsed_time:.2f} seconds")

        if response.status_code == 200:
            return response.json()  # Extracted JSON response
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None

# Example usage
result = extract_fields_from_image("Ethiopia-1.jpg")
print(result)
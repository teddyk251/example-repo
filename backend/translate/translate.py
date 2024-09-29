import boto3
from google.cloud import translate
from google.api_core.exceptions import GoogleAPIError
import os
import time
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
env_path = os.path.join(project_root, '.env')

# Load the .env file
load_dotenv(dotenv_path=env_path)

# get AWS_REGION from environment variable
AWS_REGION = os.getenv("AWS_REGION")

def translate_text(text: str = "Kwa hivyo", 
                   project_id: str = "idl-s24", 
                   source_lang: str = "sw", 
                   target_lang: str = "en", 
                   service: str = "google") -> str:
    """Translates text using either Google or Amazon Translate."""
    if source_lang == 'rw' and target_lang == 'en':
        return google_translate(text, project_id, source_lang, target_lang)
    if source_lang == 'en' and target_lang == 'rw':
        return google_translate(text, project_id, source_lang, target_lang)
    
    if service == "google":
        return google_translate(text, project_id, source_lang, target_lang)
    elif service == "amazon":
        return amazon_translate(text, source_lang, target_lang, region=AWS_REGION)
    else:
        raise ValueError("Unsupported service. Choose either 'google' or 'amazon'.")

def google_translate(text: str, project_id: str, source_lang: str, target_lang: str) -> str:
    """Uses Google Cloud Translate to translate text."""
    
    client = translate.TranslationServiceClient()
    location = "global"
    parent = f"projects/{project_id}/locations/{location}"

    try:
        response = client.translate_text(
            request={
                "parent": parent,
                "contents": [text],
                "mime_type": "text/plain",  # mime types: text/plain, text/html
                "source_language_code": source_lang,
                "target_language_code": target_lang,
            }
        )
        # Return the first translated text
        return response.translations[0].translated_text if response.translations else None
    except GoogleAPIError as e:
        print(f"Error translating text with Google: {e}")
        return None

def amazon_translate(text: str, source_lang: str, target_lang: str, region: str) -> str:
    """Uses Amazon Translate to translate text."""
    start_time = time.time()
    
    client = boto3.client('translate', region_name=AWS_REGION)
    
    try:
        response = client.translate_text(
            Text=text,
            SourceLanguageCode=source_lang,
            TargetLanguageCode=target_lang
        )
        print(f"Amazon Translate took {time.time() - start_time} seconds.")
        return response['TranslatedText']
    except Exception as e:
        print(f"Error translating text with Amazon: {e}")
        return None
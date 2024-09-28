from google.cloud import translate
from google.api_core.exceptions import GoogleAPIError

def translate_text(text: str = "Kwa hivyo", project_id: str = "idl-s24", source_lang: str = "sw", target_lang: str = "en") -> translate.TranslationServiceClient:
    """Translating Text."""

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
        print(f"Error translating text: {e}")
        return None
# tts.py
# This implements text-to-speech (TTS) functionality using OpenAI or Pindo for specific languages.

import os
import requests
import logging
import time
from openai import OpenAI
from dotenv import load_dotenv
import uuid

current_dir = os.path.dirname(os.path.abspath(__file__))
# Go up one directory to the project root
project_root = os.path.dirname(current_dir)
# Construct the path to the .env file
env_path = os.path.join(project_root, '.env')
# Load the .env file
load_dotenv(dotenv_path=env_path)

# Setup logging
logging.basicConfig(level=logging.INFO)

# Supported languages for TTS
SUPPORTED_LANGS = ["en", "rw", "sw", "fr"]
UPLOAD_FOLDER = 'uploads'
# API keys (store these securely)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Setup OpenAI TTS Client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def synthesize_speech_openai(text: str, language_code: str = "en"):
    """Synthesize speech using OpenAI API."""
    start_time = time.time()
    try:
        # Call the OpenAI TTS API
        response = openai_client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=text
        )

        # Stream the audio content directly to a file
        output_file = "output_openai.wav"
        file_path = os.path.join(UPLOAD_FOLDER, f"{output_file}_{uuid.uuid4().hex[:8]}")
        with open(file_path, "wb") as audio_file:
            for chunk in response.iter_bytes():
                audio_file.write(chunk)

        logging.info(f"OpenAI TTS audio saved to {file_path}")
        logging.info(f"OpenAI TTS took {time.time() - start_time} seconds.")
        return file_path

    except Exception as e:
        logging.error(f"Error in OpenAI TTS: {e}")
        return None


def synthesize_speech_pindo(text: str, language: str):
    """Synthesize speech using Pindo for supported languages."""
    start = time.time()
    try:
        url = "https://api.pindo.io/v1/transcription/tts"
        data = {"text": text, "lang": language}

        response = requests.post(url, json=data)
        if response.status_code == 200:
            audio_url = response.json().get("generated_audio_url")
            audio_content = requests.get(audio_url).content

            file_path = os.path.join(UPLOAD_FOLDER, f"{output_file}_{uuid.uuid4().hex[:8]}")
            with open(file_path, "wb") as audio_file:
                out.write(audio_content)
            logging.info(f"Pindo TTS audio saved to {output_file}")
            logging.info(f"Pindo TTS took {time.time() - start} seconds.")
            return file_path
        else:
            logging.error(f"Pindo TTS failed: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Error in Pindo TTS: {e}")
        return None

def synthesize_text_to_speech(text: str, language: str):
    """Main function to handle TTS based on the language."""
    
    # Validate language
    if language not in SUPPORTED_LANGS:
        raise ValueError("Unsupported language.")

    # Choose TTS service
    if language in ['rw']:
        audio_file = synthesize_speech_pindo(text, language)
    else:
        # Use OpenAI for other languages
        audio_file = synthesize_speech_openai(text, language)

    return audio_file
# stt.py
# This implements speech recognition using Whisper via Groq by default.
# For Kinyarwanda, it uses Pindo.ai

import os
import base64
import requests
import logging
from io import BytesIO
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
# Go up one directory to the project root
project_root = os.path.dirname(current_dir)
# Construct the path to the .env file
env_path = os.path.join(project_root, '.env')
# Load the .env file
load_dotenv(dotenv_path=env_path)

# Setup logging
logging.basicConfig(level=logging.INFO)

# Supported languages for transcription
SUPPORTED_LANGS = ["en", "rw", "sw", "fr"]

# API keys (store these securely)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# PINDO_API_KEY = os.getenv("PINDO_API_KEY")

def setup_groq_client():
    """Setup Groq client."""
    from groq import Groq
    return Groq(api_key=GROQ_API_KEY)

def transcribe_whisper(filename: str, language: str = "en"):
    """Transcribe audio using Whisper via Groq API."""
    try:
        client = setup_groq_client()
        with open(filename, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(filename, file.read()),
                model="whisper-large-v3",
                response_format="json",
                language=language,
                temperature=0.2
            )
        logging.info(f"Whisper transcription: {transcription.text}")
        return transcription.text
    except Exception as e:
        logging.error(f"Error in Whisper transcription: {e}")
        return "Error in transcription."

def transcribe_pindo(filename: str, language: str):
    """Transcribe audio using Pindo for supported languages."""
    try:
        url = "https://api.pindo.io/v1/transcription/stt"
        data = {"lang": language}

        with open(filename, 'rb') as audio_file:
            audio_content = audio_file.read()
        audio_file_io = BytesIO(audio_content)
        filename = os.path.basename(filename)
        files = {
            'audio': (filename, audio_file_io, 'audio/wav')
        }
        response = requests.post(url, files=files, data=data)
        print(response.status_code)
        if response.status_code == 200:
            response_json = response.json()
            logging.info(f"Pindo transcription: {response_json['text']}")
            return response_json['text']
        else:
            logging.error(f"Pindo transcription failed: {response.status_code}")
            return "Error in transcription."
    except Exception as e:
        logging.error(f"Error in Pindo transcription: {e}")
        return "Error in transcription."

def transcribe_audio(file_path: str, language: str):
    """Main function to handle audio transcription."""
    
    # Validate language
    if language not in SUPPORTED_LANGS:
        raise ValueError("Unsupported language.")

    # Choose transcription service
    if language in ['rw', 'sw']:
        transcription = transcribe_pindo(file_path, language)
    else:
        transcription = transcribe_whisper(file_path, language)

    return transcription

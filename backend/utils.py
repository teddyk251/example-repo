from flask import Flask, request, jsonify
import requests
from io import BytesIO

# def process_audio(filepath,mode,lang):
#     """
#     This function handles the audio processing
#         First transcribes the audio file
#         Returns the transcription
        
#     """
#     # TODO: Implement audio processing logic
#     # This is where you'd add your audio processing code
#     response = transcription(filepath, mode='stt', lang=lang)
#     return response['text']

def pindo(mode, filepath, lang='rw', text=None):
    url = f"https://api.pindo.io/v1/transcription/{mode}"
    if mode == 'tts':
        data = {
            "lang": lang,
            "speech_rate": 1.0,
            "text": text
        }
        response = requests.post(url, files=files, data=data)
        response = response.json()
        return response
    else:
        data = {
            "lang": lang
        }
        audio_path = filepath
        with open(audio_path, 'rb') as audio_file:
            audio_content = audio_file.read()

        audio_file_io = BytesIO(audio_content)

        files = {
            'audio': ('file.wav', audio_file_io, 'audio/wav')  # Adjust MIME type if necessary
        }

        response = requests.post(url, files=files, data=data)
        response = response.json()
        return response

def process_audio(filepath, mode='stt', lang='rw', text=None):
    '''
    Calls the Pindo API to transcribe the audio file
    If mode is 'stt', it transcribes the audio file and returns the transcription
    If mode is 'tts', it transcribes the audio file and returns the link to the generated audio file
    '''
    if mode == 'stt':
        response = pindo(mode, filepath, lang, text)
        return {"transcription": response['text']}
    elif mode == 'tts':
        response = pindo(mode, filepath, lang, text)
        return {"audio": response['generated_audio_url']}

def translate(text, source, target):
    
    # TODO: Implement text translation logic

    translated_text = f"Translated: {text}"  # This is a placeholder
    return {"translation": translated_text}


# def call_llm(text):
#     # TODO: Implement LLM logic

#     return {
#         "op_type": "chat",
#         "data": {"text": f"LLM response to: {text}"}
#     }

def call_llm(text, test_op=None):
    if test_op:
        return {
            "op_type": test_op,
            "redirect_url": "https://example.com/test",
            "data": {"text": "Test LLM response"}
        }
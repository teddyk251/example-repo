from flask import Flask, request, jsonify
import os
from utils import *
from speech.stt import transcribe_audio
from speech.tts import synthesize_text_to_speech
from translate.translate import translate_text
from rag.data_processor import run_chat_session
from dotenv import load_dotenv
from flask_cors import CORS
import uuid
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

app = Flask(__name__)
CORS(app)

current_dir = os.path.dirname(os.path.abspath(__file__))
# Go up one directory to the project root
project_root = os.path.dirname(current_dir)
# Construct the path to the .env file
env_path = os.path.join(project_root, '.env')
# Load the .env file
load_dotenv(dotenv_path=env_path)
cloudinary_key = os.getenv("CLOUDINARY_SECRET")
# Configuration
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configuration       
cloudinary.config( 
    cloud_name = "dlu3m1ulr", 
    api_key = "536255541225145", 
    api_secret = cloudinary_key, # Click 'View API Keys' above to copy your API secret
    secure=True
)

@app.route('/test', methods=['GET'])
def test():
    return jsonify({"message": "Test successful"}), 200

# @app.route('/submit-form', methods=['POST'])
# def submit_form():
#     try:
#         form_data = {}
        
#         # Process form fields and audio files
#         for field, files in request.files.lists():
#             transcriptions = []
#             for file in files:
#                 if file.filename:
#                     filename = secure_filename(file.filename)
#                     file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#                     file.save(file_path)
#                     if file.filename.lower().endswith(('.wav', '.mp3', '.ogg')):
#                         # Determine language (you might want to pass this as a parameter)
#                         lang = 'en'  # or 'rw' for Kinyarwanda
#                         transcription = transcribe_audio(file_path, lang)
#                         if lang != 'en':
#                             # Translate to English if not already in English
#                             transcription = translate_text(transcription, source_lang=lang, target_lang='en', service='amazon')
#                         transcriptions.append(transcription)
#                     os.remove(file_path)  # Remove file after processing
#             form_data[field] = transcriptions if transcriptions else request.form.getlist(field)

#         # Process OCR image
#         ocr_image = request.files.get('ocrImage')
#         if ocr_image:
#             file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#             ocr_image.save(file_path)
#             ocr_text = process_image_ocr(file_path)
#             form_data['ocrText'] = ocr_text
#             os.remove(file_path)  # Remove file after processing

#         return jsonify({"result": form_data}), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

@app.route('/process', methods=['POST'])
def process_input():
    try:
        lang = request.args.get('lang', 'en')
        
        if 'file' in request.files:
            return handle_audio_input(request.files['file'], lang)
        elif request.is_json:
            return handle_text_input(request.get_json(), lang)
        else:
            return jsonify({"error": "Invalid input. Please send either an audio file or JSON data."}), 400
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

def handle_audio_input(file, lang):
    if not file:
        return jsonify( {"error": "No file content"}), 400
    
    filename = file.filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        file.save(filepath)
        transcription = transcribe_audio(filepath, lang)
        if lang != 'en':
            translation = translate_text(transcription, source_lang=lang, target_lang='en', service='amazon')
            text_for_llm = translation
        else:
            text_for_llm = transcription
        llm_response = run_chat_session(text_for_llm)
        
        if llm_response['op_type'] in ['new', 'renew']:
            return jsonify({"redirect_url": llm_response['redirect_url']})
        elif llm_response['op_type'] == 'chat':
            if lang != 'en':
                translation = translate_text(llm_response['data'], source_lang='en', target_lang=lang,service='amazon')        
                text_for_tts = translation
            else:
                text_for_tts = llm_response['data']
            tts_response = synthesize_text_to_speech(text_for_tts, language=lang)
            unique_filename = f"{filename}_{uuid.uuid4().hex[:8]}.wav"
            # Upload audio
            upload_result = cloudinary.uploader.upload(tts_response,
            resource_type="auto",
            public_id=f"audios/{tts_response}",
            format="wav")
            return jsonify({"audio": upload_result["secure_url"]})
        else:
            return jsonify({"error": "Invalid operation type from LLM"}), 500
    except Exception as e:
        return jsonify({"error": f"Error processing audio: {str(e)}"}), 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


def handle_text_input(data, lang):
    try:
        if 'text' not in data:
            return jsonify({"error": "No text field in JSON data"}), 400
        
        text = data['text']
        if lang != 'en':
            translation = translate_text(text, source_lang=lang, target_lang='en', service='amazon')
            text_for_llm = translation
        else:
            text_for_llm = text
        
        llm_response = run_chat_session(text_for_llm)
        
        if llm_response['op_type'] in ['new', 'renew']:
            return jsonify({"redirect_url": llm_response['redirect_url']})
        elif llm_response['op_type'] == 'chat':
            if lang != 'en':
                translation = translate_text(llm_response['data'], source_lang='en', target_lang=lang, service='amazon')
                response_text = translation
            else:
                response_text = llm_response['data']
            return jsonify({"response": response_text})
        else:
            return jsonify({"error": "Invalid operation type from LLM"}), 500
    except Exception as e:
        return jsonify({"error": f"Error processing text: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True)
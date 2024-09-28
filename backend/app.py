from flask import Flask, request, jsonify
import os
from utils import *

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# @app.route('/process', methods=['POST'])
# def process_input():
#     try:
#         # Get the language from the request query parameters
#         lang = request.args.get('lang', 'en')
#         if 'file' in request.files:
#             # Handle audio file upload
#             # If the input is an audio file, we need to transcribe it and pass it to the LLM
#             file = request.files['file']
#             if file:
#                 filename = file.filename
#                 filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#                 file.save(filepath)
#                 try:
#                     transcription = process_audio(filepath,lang,mode='stt')
#                     if lang != 'en':
#                         translation = translate(transcription, source=lang, target='en') # Translate to English
#                     llm_response = call_llm(transcription)
#                     # Expected format of llm_response: {"op_type": "new", "redirect_url": "https://example.com", "data": {"text": "Hello world!"}}
#                     if llm_response['op_type'] == 'new':
#                         # If the LLM response is to create a new resource, we return the redirect URL
#                         pass
#                     elif llm_response['op_type'] == 'renew':
#                         # If the LLM response is to update an existing resource, we return the redirect URL
#                         pass
#                     else:  #llm_response['op_type'] == 'chat'
#                         if lang != 'en':
#                             translation = translate(llm_response['data']['text'], source='en', target=lang) # Translate back to the original language
#                         response = process_audio(filepath=None, lang=lang, mode='tts', text=translation['translation']) # Generate audio file url
#                         audio_url = response['audio']
#                         return jsonify({"audio": audio_url})

                            

#                 except Exception as e:
#                     return jsonify({"error": f"Error processing audio: {str(e)}"}), 500
#                 finally:
#                     # Clean up the file after processing
#                     if os.path.exists(filepath):
#                         os.remove(filepath)
#             else:
#                 return jsonify({"error": "No file content"}), 400
#         elif request.is_json:
#             # Handle JSON input
#             # If the input is text, this means we need to translate depending on the language and pass it to the LLM
#             data = request.get_json()
#             return process_text(data)
#         else:
#             return jsonify({"error": "Invalid input. Please send either an audio file or JSON data."}), 400
#     except Exception as e:
#         return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@app.route('/process', methods=['POST'])
def process_input():
    try:
        lang = request.args.get('lang', 'en')
        print(lang)
        
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
        return jsonify({"error": "No file content"}), 400
    
    filename = file.filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        file.save(filepath)
        transcription = process_audio(filepath, lang, mode='stt')
        
        if lang != 'en':
            translation = translate(transcription['transcription'], source=lang, target='en')
            text_for_llm = translation['translation']
        else:
            text_for_llm = transcription['transcription']
        test_llm_op = request.args.get('test_llm_op')
        llm_response = call_llm(text_for_llm, test_op=test_llm_op)
        # llm_response = call_llm(text_for_llm)
        
        if llm_response['op_type'] in ['new', 'renew']:
            return jsonify({"redirect_url": llm_response['redirect_url']})
        elif llm_response['op_type'] == 'chat':
            if lang != 'en':
                translation = translate(llm_response['data']['text'], source='en', target=lang)
                text_for_tts = translation['translation']
            else:
                text_for_tts = llm_response['data']['text']
            
            tts_response = process_audio(filepath=None, lang=lang, mode='tts', text=text_for_tts)
            return jsonify({"audio": tts_response['audio']})
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
            translation = translate(text, source=lang, target='en')
            text_for_llm = translation['translation']
        else:
            text_for_llm = text
        
        llm_response = call_llm(text_for_llm)
        
        if llm_response['op_type'] in ['new', 'renew']:
            return jsonify({"redirect_url": llm_response['redirect_url']})
        elif llm_response['op_type'] == 'chat':
            if lang != 'en':
                translation = translate(llm_response['data']['text'], source='en', target=lang)
                response_text = translation['translation']
            else:
                response_text = llm_response['data']['text']
            return jsonify({"response": response_text})
        else:
            return jsonify({"error": "Invalid operation type from LLM"}), 500
    except Exception as e:
        return jsonify({"error": f"Error processing text: {str(e)}"}), 500

# def process_text(data):
#     """"
#     If the input is text, this means we need to translate depending on the language and pass it to the LLM
#     """
#     try:
#         if 'text' in data:
#             # Example: just return the text length
#             return jsonify({"message": f"Processed text of length: {len(data['text'])}"})
#         else:
#             return jsonify({"error": "No text field in JSON data"}), 400
#     except Exception as e:
#         return jsonify({"error": f"Error processing text: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
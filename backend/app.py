from flask import Flask, request, jsonify
import os
from utils import *
from speech.stt import transcribe_audio
from speech.tts import synthesize_text_to_speech
from translate.translate import translate_text
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()

# Configuration
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


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
        return jsonify({"error": "No file content"}), 400
    
    filename = file.filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        file.save(filepath)
        # transcription = process_audio(filepath, lang=lang, mode='stt')
        transcription = transcribe_audio(filepath, lang)
        print(transcription)
        if lang != 'en':
            translation = translate_text(transcription, source_lang=lang, target_lang='en')

            print(translation)
            text_for_llm = translation
        else:
            text_for_llm = transcription
        llm_response = call_llm(text_for_llm, test_op='chat')
        print(llm_response)
        
        if llm_response['op_type'] in ['new', 'renew']:
            return jsonify({"redirect_url": llm_response['redirect_url']})
        elif llm_response['op_type'] == 'chat':
            if lang != 'en':
                translation = translate_text(llm_response['data']['text'], source_lang='en', target_lang=lang)
                text_for_tts = translation
                print(text_for_tts)
            else:
                text_for_tts = llm_response['data']['text']
            tts_response = synthesize_text_to_speech(text_for_tts, language=lang)
            # tts_response = process_audio(filepath=None, lang=lang, mode='tts', text=text_for_tts)
            return jsonify({"audio": tts_response})
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
            translation = translate_text(text, source_lang=lang, target_lang='en')
            text_for_llm = translation
        else:
            text_for_llm = text
        
        llm_response = call_llm(text_for_llm, test_op='chat')
        
        if llm_response['op_type'] in ['new', 'renew']:
            return jsonify({"redirect_url": llm_response['redirect_url']})
        elif llm_response['op_type'] == 'chat':
            if lang != 'en':
                translation = translate_text(llm_response['data']['text'], source_lang='en', target_lang=lang)
                response_text = translation
            else:
                response_text = llm_response['data']['text']
            return jsonify({"response": response_text})
        else:
            return jsonify({"error": "Invalid operation type from LLM"}), 500
    except Exception as e:
        return jsonify({"error": f"Error processing text: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True)
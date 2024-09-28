from stt import transcribe_audio

transcription = transcribe_audio("speech/output_converted.wav", "rw")
print(f"Transcription: {transcription}")
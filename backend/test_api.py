import unittest
import requests
import os

class TestAPIWorkflow(unittest.TestCase):
    BASE_URL = "http://localhost:5000/process"

    def test_text_input_english(self):
        payload = {"text": "This is a test sentence in English."}
        response = requests.post(f"{self.BASE_URL}?lang=en", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('response', data)

    def test_text_input_non_english(self):
        payload = {"text": "Ceci est une phrase de test en français."}
        response = requests.post(f"{self.BASE_URL}?lang=fr", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('response', data)

    def test_audio_input_english(self):
        audio_file_path = '/Users/teddy/Downloads/F_0101 10y4m.wav'
        if not os.path.exists(audio_file_path):
            self.skipTest(f"Test audio file not found: {audio_file_path}")
        
        with open(audio_file_path, 'rb') as audio_file:
            files = {'file': audio_file}
            response = requests.post(f"{self.BASE_URL}?lang=en", files=files)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue('audio' in data or 'redirect_url' in data)

    def test_audio_input_non_english(self):
        audio_file_path = '/Users/teddy/Downloads/French Anywhere will do.wav'
        if not os.path.exists(audio_file_path):
            self.skipTest(f"Test audio file not found: {audio_file_path}")
        
        with open(audio_file_path, 'rb') as audio_file:
            files = {'file': audio_file}
            response = requests.post(f"{self.BASE_URL}?lang=fr", files=files)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue('audio' in data or 'redirect_url' in data)

    def test_invalid_input(self):
        response = requests.post(self.BASE_URL)
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_missing_text(self):
        payload = {}
        response = requests.post(self.BASE_URL, json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_llm_new_operation(self):
        # This test assumes you can control the LLM response for testing
        # You might need to modify your LLM function to accept a test flag
        payload = {"text": "Create a new resource"}
        response = requests.post(f"{self.BASE_URL}?lang=en&test_llm_op=new", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('redirect_url', data)

    def test_llm_renew_operation(self):
        # Similar to the new operation test
        payload = {"text": "Update an existing resource"}
        response = requests.post(f"{self.BASE_URL}?lang=en&test_llm_op=renew", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('redirect_url', data)

if __name__ == '__main__':
    unittest.main()
import unittest
from unittest.mock import patch, MagicMock
from google.api_core.exceptions import GoogleAPIError
from translate import translate_text


class TestTranslateText(unittest.TestCase):

    @patch('google.cloud.translate.TranslationServiceClient')
    def test_successful_translation_en_to_sw(self, mock_client):
        """Test successful translation from Swahili to English."""
        mock_response = MagicMock()
        mock_response.translations = [MagicMock(translated_text="Hi. I want some help with processing a visa")]
        mock_client.return_value.translate_text.return_value = mock_response

        result = translate_text("Habari. Ninataka usaidizi wa kushughulikia visa", "idl-s24", "sw", "en")
        self.assertEqual(result, "Hi. I want some help with processing a visa")

    @patch('google.cloud.translate.TranslationServiceClient')
    def test_successful_translation_en_to_rw(self, mock_client):
        """Test successful translation from English to Kinyarwanda."""
        mock_response = MagicMock()
        mock_response.translations = [MagicMock(translated_text="Kubwibyo")]
        mock_client.return_value.translate_text.return_value = mock_response

        result = translate_text("Therefore", "idl-s24", "en", "rw")
        self.assertEqual(result, "Kubwibyo")

    @patch('google.cloud.translate.TranslationServiceClient')
    def test_empty_translation(self, mock_client):
        """Test case where the translation response is empty."""
        mock_response = MagicMock()
        mock_response.translations = []
        mock_client.return_value.translate_text.return_value = mock_response

        result = translate_text("Kwa hivyo", "idl-s24", "sw", "en")
        self.assertIsNone(result)

    @patch('google.cloud.translate.TranslationServiceClient')
    def test_translation_error(self, mock_client):
        """Test case where the translation service throws an error."""
        mock_client.return_value.translate_text.side_effect = GoogleAPIError("API error")

        result = translate_text("Kwa hivyo", "idl-s24", "sw", "en")
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()

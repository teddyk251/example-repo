import unittest
from unittest.mock import patch, MagicMock
from google.api_core.exceptions import GoogleAPIError
from translate import translate_text


class TestTranslateText(unittest.TestCase):

    @patch('google.cloud.translate.TranslationServiceClient')
    def test_successful_translation_google(self, mock_client):
        """Test successful translation from Swahili to English using Google Translate."""
        mock_response = MagicMock()
        mock_response.translations = [MagicMock(translated_text="Hi. I want some help with processing a visa")]
        mock_client.return_value.translate_text.return_value = mock_response

        result = translate_text("Habari. Ninataka usaidizi wa kushughulikia visa", 
                                "idl-s24", "sw", "en", service="google")
        self.assertEqual(result, "Hi. I want some help with processing a visa")

    @patch('google.cloud.translate.TranslationServiceClient')
    def test_empty_translation_google(self, mock_client):
        """Test case where the Google Translate response is empty."""
        mock_response = MagicMock()
        mock_response.translations = []
        mock_client.return_value.translate_text.return_value = mock_response

        result = translate_text("Kwa hivyo", "idl-s24", "sw", "en", service="google")
        self.assertIsNone(result)

    @patch('google.cloud.translate.TranslationServiceClient')
    def test_translation_error_google(self, mock_client):
        """Test case where Google Translate throws an API error."""
        mock_client.return_value.translate_text.side_effect = GoogleAPIError("API error")

        result = translate_text("Kwa hivyo", "idl-s24", "sw", "en", service="google")
        self.assertIsNone(result)

    @patch('boto3.client')
    def test_successful_translation_amazon(self, mock_boto_client):
        """Test successful translation from Swahili to English using Amazon Translate."""
        # Mock the response from boto3 client
        mock_response = {"TranslatedText": "Hi. I want some help with processing a visa"}
        mock_boto_client.return_value.translate_text.return_value = mock_response

        result = translate_text("Habari. Ninataka usaidizi wa kushughulikia visa", 
                                "idl-s24", "sw", "en", service="amazon")
        # Now compare with the actual translation
        self.assertEqual(result, "Hi. I want some help with processing a visa")

    @patch('boto3.client')
    def test_translation_error_amazon(self, mock_boto_client):
        """Test case where Amazon Translate throws an error."""
        mock_boto_client.return_value.translate_text.side_effect = Exception("API error")

        result = translate_text("Kwa hivyo", "idl-s24", "sw", "en", service="amazon")
        self.assertIsNone(result)


if __name__ == '__main__':
    # unittest.main()
    sample = "Habari. Ninataka usaidizi wa kushughulikia visa"
    print(translate_text(sample, "idl-s24", "sw", "en", service="google"))

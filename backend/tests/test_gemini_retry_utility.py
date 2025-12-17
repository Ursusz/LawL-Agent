import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add backend/src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from utilities.gemini_utils import call_gemini_with_retry

class TestGeminiRetry(unittest.TestCase):
    
    @patch('utilities.gemini_utils.time.sleep')
    def test_success_first_try(self, mock_sleep):
        mock_func = MagicMock(return_value="Success")
        result = call_gemini_with_retry(mock_func)
        self.assertEqual(result, "Success")
        mock_func.assert_called_once()
        mock_sleep.assert_not_called()

    @patch('utilities.gemini_utils.time.sleep')
    def test_retry_on_unavailable(self, mock_sleep):
        mock_func = MagicMock(side_effect=[Exception("503 UNAVAILABLE"), "Success"])
        result = call_gemini_with_retry(mock_func)
        self.assertEqual(result, "Success")
        self.assertEqual(mock_func.call_count, 2)
        mock_sleep.assert_called_once_with(65) # Default delay

    @patch('utilities.gemini_utils.time.sleep')
    def test_retry_on_429_with_parsed_delay(self, mock_sleep):
        # "Please retry in 10s"
        mock_func = MagicMock(side_effect=[Exception("429 RESOURCE_EXHAUSTED Please retry in 10s"), "Success"])
        result = call_gemini_with_retry(mock_func)
        self.assertEqual(result, "Success")
        self.assertEqual(mock_func.call_count, 2)
        mock_sleep.assert_called_once_with(11.0) # 10 + 1 buffer

    @patch('utilities.gemini_utils.time.sleep')
    def test_max_retries_exceeded(self, mock_sleep):
        mock_func = MagicMock(side_effect=Exception("UNAVAILABLE"))
        result = call_gemini_with_retry(mock_func, max_retries=3)
        self.assertIsNone(result)
        self.assertEqual(mock_func.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch('utilities.gemini_utils.time.sleep')
    def test_non_retriable_error(self, mock_sleep):
        mock_func = MagicMock(side_effect=Exception("ValueError: Invalid input"))
        result = call_gemini_with_retry(mock_func)
        self.assertIsNone(result)
        mock_func.assert_called_once()
        mock_sleep.assert_not_called()

if __name__ == '__main__':
    unittest.main()

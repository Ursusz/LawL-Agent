
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

from backend.src.search_laws import find_laws, fetch_online_reference

class TestSearchLaws(unittest.TestCase):

    @patch('backend.src.search_laws.brave_search_api')
    @patch('backend.src.search_laws.cloud_file_management')
    @patch('backend.src.search_laws.bm25')
    @patch('backend.src.search_laws.gemini_summary')
    def test_find_laws_online_search_missing_url(self, mock_gemini, mock_bm25, mock_cloud, mock_brave):
        # Setup mocks
        law_ref = "TEST_LAW_123"
        document_text = "Some context"
        
        # Mock cloud search to return None ALWAYS (simulating race condition where file is not yet indexed)
        mock_cloud.search_file_in_cloud.return_value = None
        
        # Mock brave search to return the file ID directly (simulating successful save)
        mock_brave.search_law_online.return_value = 'new_file_id'

        # Mock cloud download to return content with URL on first line
        expected_url = "https://example.com/law"
        file_content = f"{expected_url}\nLaw text content"
        mock_cloud.download_file_content.return_value = file_content
        
        # Mock BM25 and Gemini
        mock_bm25.get_most_relevant_fragment.return_value = "Relevant article"
        mock_gemini.get_gemini_informations_about_law.return_value = ["Summary", "Simplified", "Article Summary"]
        
        # Run the function
        results = find_laws([law_ref], document_text)
        
        # Verify results
        self.assertIn(law_ref, results)
        law_details = results[law_ref]
        
        # This assertion is expected to FAIL before the fix
        self.assertEqual(law_details['url'], expected_url)
        self.assertEqual(law_details['law'], "Law text content")

if __name__ == '__main__':
    unittest.main()

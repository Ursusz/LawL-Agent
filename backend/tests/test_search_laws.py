import unittest
from unittest.mock import MagicMock, patch
import sys
import os

from src.search_laws import find_laws, fetch_online_reference

class TestSearchLaws(unittest.TestCase):

    @patch('src.search_laws.brave_search_api')
    @patch('src.search_laws.cloud_file_management')
    @patch('src.search_laws.bm25')
    @patch('src.search_laws.gemini_summary')
    def test_multiple_references_mixed_sources(self, mock_gemini, mock_bm25, mock_cloud, mock_brave):
        """Test processing multiple law references from both cache and online sources"""
        law_refs = ["LEGE_53_2003", "HG_856_2020", "OUG_195_2002"]
        document_text = "Context about labor law and government decisions"
        
        # Mock cloud search: first found in cache, second not found, third found
        def cloud_search_side_effect(filename):
            if 'LEGE_53_2003' in filename:
                return {'id': 'cached_lege_id'}
            elif 'HG_856_2020' in filename:
                return None  # Not in cache
            elif 'OUG_195_2002' in filename:
                return {'id': 'cached_oug_id'}
            return None
        
        mock_cloud.search_file_in_cloud.side_effect = cloud_search_side_effect
        
        # Mock brave search: only called for HG_856_2020
        def brave_search_side_effect(ref):
            if 'HG_856_2020' in ref:
                return 'online_hg_id'
            return None
        
        mock_brave.search_law_online.side_effect = brave_search_side_effect
        
        # Mock cloud download with proper content including all references
        def download_side_effect(file_id):
            if file_id == 'cached_lege_id':
                return "https://legislatie.just.ro/Public/DetaliiDocument/41500\nLEGE nr. 53 din 24 ianuarie 2003\nArt. 1..."
            elif file_id == 'online_hg_id':
                return "https://legislatie.just.ro/Public/DetaliiDocument/229594\nHOTĂRÂRE nr. 856 din 2 septembrie 2020\nArt. 1..."
            elif file_id == 'cached_oug_id':
                return "https://legislatie.just.ro/Public/DetaliiDocument/37565\nORDONANȚĂ DE URGENȚĂ nr. 195 din 12 decembrie 2002\nArt. 1..."
            return ""
        
        mock_cloud.download_file_content.side_effect = download_side_effect
        
        # Mock BM25 and Gemini
        mock_bm25.get_most_relevant_fragment.return_value = "Art. 5..."
        mock_gemini.get_gemini_informations_about_law.return_value = ["Summary", "Simplified", "Article Summary"]
        
        # Run
        results = find_laws(law_refs, document_text)
        
        # Verify all three laws processed
        self.assertEqual(len(results), 3)
        self.assertIn("LEGE_53_2003", results)
        self.assertIn("HG_856_2020", results)
        self.assertIn("OUG_195_2002", results)
        
        # Verify URLs present
        self.assertIn("legislatie.just.ro", results["LEGE_53_2003"]["url"])
        self.assertIn("legislatie.just.ro", results["HG_856_2020"]["url"])
        self.assertIn("legislatie.just.ro", results["OUG_195_2002"]["url"])
        
        # Verify brave search only called once (for HG_856_2020)
        self.assertEqual(mock_brave.search_law_online.call_count, 1)

    @patch('src.search_laws.brave_search_api')
    @patch('src.search_laws.cloud_file_management')
    @patch('src.search_laws.bm25')
    @patch('src.search_laws.gemini_summary')
    def test_cache_hit(self, mock_gemini, mock_bm25, mock_cloud, mock_brave):
        """Test law found in cache (no online search needed)"""
        law_ref = "LEGE_287_2009"
        document_text = "Context"
        
        # Mock cache hit
        mock_cloud.search_file_in_cloud.return_value = {'id': 'cached_id'}
        mock_cloud.download_file_content.return_value = "https://legislatie.just.ro/Public/DetaliiDocument/109891\nLEGE nr. 287 din 17 iulie 2009\nArt. 1..."
        
        mock_bm25.get_most_relevant_fragment.return_value = "Art. 1..."
        mock_gemini.get_gemini_informations_about_law.return_value = ["Summary", "Simple", "Art Sum"]
        
        results = find_laws([law_ref], document_text)
        
        # Verify result
        self.assertIn(law_ref, results)
        self.assertEqual(results[law_ref]['url'], "https://legislatie.just.ro/Public/DetaliiDocument/109891")
        
        # Verify online search NOT called
        mock_brave.search_law_online.assert_not_called()

    @patch('src.search_laws.brave_search_api')
    @patch('src.search_laws.cloud_file_management')
    @patch('src.search_laws.bm25')
    @patch('src.search_laws.gemini_summary')
    def test_cache_miss_online_found(self, mock_gemini, mock_bm25, mock_cloud, mock_brave):
        """Test law not in cache but found online"""
        law_ref = "LEGE_360_2023"
        document_text = "Context"
        
        # Mock cache miss
        mock_cloud.search_file_in_cloud.return_value = None
        
        # Mock online search success
        mock_brave.search_law_online.return_value = 'new_online_id'
        mock_cloud.download_file_content.return_value = "https://legislatie.just.ro/Public/DetaliiDocument/272583\nLEGE nr. 360 din 28 decembrie 2023\nArt. 1..."
        
        mock_bm25.get_most_relevant_fragment.return_value = "Art. 1..."
        mock_gemini.get_gemini_informations_about_law.return_value = ["Summary", "Simple", "Art Sum"]
        
        results = find_laws([law_ref], document_text)
        
        # Verify result
        self.assertIn(law_ref, results)
        self.assertEqual(results[law_ref]['url'], "https://legislatie.just.ro/Public/DetaliiDocument/272583")
        
        # Verify online search WAS called
        mock_brave.search_law_online.assert_called_once()

    @patch('src.search_laws.brave_search_api')
    @patch('src.search_laws.cloud_file_management')
    @patch('src.search_laws.bm25')
    @patch('src.search_laws.gemini_summary')
    def test_not_found_anywhere(self, mock_gemini, mock_bm25, mock_cloud, mock_brave):
        """Test law not found in cache or online"""
        law_ref = "LEGE_0_0000"
        document_text = "Context"
        
        mock_cloud.search_file_in_cloud.return_value = None
        mock_brave.search_law_online.return_value = None
        
        results = find_laws([law_ref], document_text)
        
        # Should not be in results (no law_text means skipped)
        self.assertNotIn(law_ref, results)

    @patch('src.search_laws.brave_search_api')
    @patch('src.search_laws.cloud_file_management')
    @patch('src.search_laws.bm25')
    @patch('src.search_laws.gemini_summary')
    def test_gemini_failure(self, mock_gemini, mock_bm25, mock_cloud, mock_brave):
        """Test handling of Gemini API failure"""
        law_ref = "OUG_117_2022"
        document_text = "Context"
        
        mock_cloud.search_file_in_cloud.return_value = {'id': 'id'}
        mock_cloud.download_file_content.return_value = "url\nORDONANȚĂ DE URGENȚĂ nr. 117 din 14 septembrie 2022\nArt. 1..."
        mock_bm25.get_most_relevant_fragment.return_value = "Art. 1"
        
        # Mock Gemini failure
        mock_gemini.get_gemini_informations_about_law.return_value = None
        
        results = find_laws([law_ref], document_text)
        
        self.assertIn(law_ref, results)
        self.assertIn("ERROR", results[law_ref])
        self.assertIn("Gemini did not return any answer", results[law_ref]["ERROR"])

if __name__ == '__main__':
    unittest.main()

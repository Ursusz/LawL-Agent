import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from src.utilities import law_reference_mappings


class TestDeduplication(unittest.IsolatedAsyncioTestCase):
    """Test that references mapping to the same law are deduplicated"""
    
    async def test_duplicate_references_deduplicated(self):
        """Test that Codul_fiscal and LEGE_227_2015 are deduplicated"""
        
        # Mock the mapping to show Codul_fiscal -> LEGE_227_2015
        with patch.object(law_reference_mappings, 'get_normalized_reference') as mock_get:
            def mock_mapping(ref):
                if ref.lower() == 'codul_fiscal':
                    return 'LEGE_227_2015'
                return None
            
            mock_get.side_effect = mock_mapping
            
            # Simulate the deduplication logic from process_file.py
            references = ['Codul_fiscal', 'LEGE_227_2015']
            
            normalized_to_originals = {}
            for ref in references:
                mapped_ref = law_reference_mappings.get_normalized_reference(ref)
                normalized_ref = mapped_ref if mapped_ref else ref
                
                if normalized_ref not in normalized_to_originals:
                    normalized_to_originals[normalized_ref] = []
                normalized_to_originals[normalized_ref].append(ref)
            
            unique_refs = list(normalized_to_originals.keys())
            
            # Verify deduplication worked
            self.assertEqual(len(unique_refs), 1, "Should have only 1 unique reference")
            self.assertIn('LEGE_227_2015', unique_refs, "Should keep the normalized reference")
            
            # Verify both original references map to the same normalized reference
            self.assertEqual(len(normalized_to_originals['LEGE_227_2015']), 2)
            self.assertIn('Codul_fiscal', normalized_to_originals['LEGE_227_2015'])
            self.assertIn('LEGE_227_2015', normalized_to_originals['LEGE_227_2015'])
    
    async def test_no_deduplication_when_no_duplicates(self):
        """Test that references without duplicates are not affected"""
        
        with patch.object(law_reference_mappings, 'get_normalized_reference') as mock_get:
            mock_get.return_value = None  # No mappings
            
            references = ['LEGE_53_2003', 'LEGE_227_2015']
            
            normalized_to_originals = {}
            for ref in references:
                mapped_ref = law_reference_mappings.get_normalized_reference(ref)
                normalized_ref = mapped_ref if mapped_ref else ref
                
                if normalized_ref not in normalized_to_originals:
                    normalized_to_originals[normalized_ref] = []
                normalized_to_originals[normalized_ref].append(ref)
            
            unique_refs = list(normalized_to_originals.keys())
            
            # Verify no deduplication occurred
            self.assertEqual(len(unique_refs), 2, "Should have 2 unique references")
            self.assertIn('LEGE_53_2003', unique_refs)
            self.assertIn('LEGE_227_2015', unique_refs)
    
    async def test_result_expansion(self):
        """Test that results are correctly expanded to all original references"""
        
        # Simulate the result expansion logic
        normalized_to_originals = {
            'LEGE_227_2015': ['Codul_fiscal', 'LEGE_227_2015']
        }
        
        # Mock law results (what find_laws would return)
        laws = {
            'LEGE_227_2015': {
                'law': 'Test law text',
                'url': 'https://example.com',
                'law_summary': 'Test summary'
            }
        }
        
        # Expand results back to all original references
        expanded_laws = {}
        for normalized_ref, original_refs in normalized_to_originals.items():
            if normalized_ref in laws:
                for original_ref in original_refs:
                    expanded_laws[original_ref] = laws[normalized_ref]
        
        # Verify both original references have the same data
        self.assertEqual(len(expanded_laws), 2)
        self.assertIn('Codul_fiscal', expanded_laws)
        self.assertIn('LEGE_227_2015', expanded_laws)
        self.assertEqual(expanded_laws['Codul_fiscal'], expanded_laws['LEGE_227_2015'])
        self.assertEqual(expanded_laws['Codul_fiscal']['law'], 'Test law text')


if __name__ == '__main__':
    unittest.main()

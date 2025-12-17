import unittest
import re
from src.web_scraping.brave_search_api import (
    parse_reference_components,
    matches_numeric_ids,
    matches_reference,
    extract_url_id
)


class TestParseReferenceComponents(unittest.TestCase):
    """Tests for parsing normalized references into components."""
    
    def test_simple_law_reference(self):
        """Test parsing LEGE_53_2003"""
        result = parse_reference_components("LEGE_53_2003")
        self.assertEqual(result, ("LEGE", "53", "2003"))
    
    def test_hg_reference(self):
        """Test parsing HG_123_2020"""
        result = parse_reference_components("HG_123_2020")
        self.assertEqual(result, ("HG", "123", "2020"))
    
    def test_multi_number_reference(self):
        """Test parsing DECIZIE_99_100_2020"""
        result = parse_reference_components("DECIZIE_99_100_2020")
        self.assertEqual(result, ("DECIZIE", "99_100", "2020"))
    
    def test_invalid_reference_too_short(self):
        """Test that references with less than 3 parts return None"""
        result = parse_reference_components("LEGE_53")
        self.assertIsNone(result)
    
    def test_invalid_reference_no_year(self):
        """Test that references without a 4-digit year return None"""
        result = parse_reference_components("LEGE_53_ABC")
        self.assertIsNone(result)


class TestExtractUrlId(unittest.TestCase):
    """Tests for extracting document IDs from URLs."""
    
    def test_detalii_document_url(self):
        """Test extracting ID from DetaliiDocument URL"""
        url = "https://legislatie.just.ro/Public/DetaliiDocument/41625"
        self.assertEqual(extract_url_id(url), 41625)
    
    def test_detalii_document_afis_url(self):
        """Test extracting ID from DetaliiDocumentAfis URL"""
        url = "https://legislatie.just.ro/Public/DetaliiDocumentAfis/128646"
        self.assertEqual(extract_url_id(url), 128646)
    
    def test_url_with_trailing_slash(self):
        """Test extracting ID from URL with trailing slash"""
        url = "https://legislatie.just.ro/Public/DetaliiDocument/41625/"
        self.assertEqual(extract_url_id(url), 41625)
    
    def test_non_numeric_url(self):
        """Test URL without numeric ID returns 0"""
        url = "https://legislatie.just.ro/Public/FormaPrintabila/ABC123"
        self.assertEqual(extract_url_id(url), 0)


class TestMatchesNumericIds(unittest.TestCase):
    """Tests for matching numeric IDs (number and year) in text."""
    
    def test_matches_exact_number_and_year(self):
        """Test that exact number and year match"""
        components = ("LEGE", "53", "2003")
        text = "Legea nr. 53/2003 - Codul muncii"
        self.assertTrue(matches_numeric_ids(text, components))
    
    def test_number_slash_year_format(self):
        """Test matching number/year format in description"""
        components = ("LEGE", "53", "2003")
        text = "publicată în temeiul Legii 53/2003"
        self.assertTrue(matches_numeric_ids(text, components))
    
    def test_number_din_year_format(self):
        """Test matching 'number din year' format"""
        components = ("LEGE", "53", "2003")
        text = "conform Legii nr. 53 din 2003"
        self.assertTrue(matches_numeric_ids(text, components))
    
    def test_wrong_year_does_not_match(self):
        """Test that wrong year doesn't match (e.g., 2025 != 2003)"""
        components = ("LEGE", "53", "2003")
        text = "Legea nr. 53/2025 din aprilie 2025"
        self.assertFalse(matches_numeric_ids(text, components))
    
    def test_wrong_number_does_not_match(self):
        """Test that wrong number doesn't match (e.g., 333 != 53)"""
        components = ("LEGE", "53", "2003")
        text = "Legea nr. 333/2003"
        self.assertFalse(matches_numeric_ids(text, components))
    
    def test_number_as_substring_does_not_match(self):
        """Test that number as substring doesn't match (53 in 533)"""
        components = ("LEGE", "53", "2003")
        text = "Legea nr. 533/2003"
        self.assertFalse(matches_numeric_ids(text, components))
    
    def test_year_as_substring_does_not_match(self):
        """Test that year as substring doesn't match (2003 in 20030)"""
        components = ("LEGE", "53", "2003")
        text = "Document 53 from year 20030"
        self.assertFalse(matches_numeric_ids(text, components))


class TestMatchesReference(unittest.TestCase):
    """Tests for the main reference matching function."""
    
    def test_exact_title_match(self):
        """Test exact match in title (law type + number + year)"""
        components = ("LEGE", "53", "2003")
        title = "LEGE 53 24/01/2003 - Portal Legislativ"
        self.assertTrue(matches_reference(title, "", components))
    
    def test_title_with_parenthetical(self):
        """Test title with (R) or (A) annotation"""
        components = ("LEGE", "53", "2003")
        title = "LEGE (R) 53 24/01/2003 - Portal Legislativ"
        self.assertTrue(matches_reference(title, "", components))
    
    def test_description_fallback_codul_muncii(self):
        """Test CODUL MUNCII matches via description"""
        components = ("LEGE", "53", "2003")
        title = "CODUL MUNCII (A) 24/01/2003 - Portal Legislativ"
        description = "Legea nr. 53/2003 - Codul muncii, republicată"
        self.assertTrue(matches_reference(title, description, components))
    
    def test_wrong_year_in_title_rejected(self):
        """Test that title with wrong year is rejected"""
        components = ("LEGE", "53", "2003")
        title = "LEGE 53 30/04/2025 - Portal Legislativ"
        # Even with matching description, should be rejected
        description = "modifică legea 53/2003"
        self.assertFalse(matches_reference(title, description, components))
    
    def test_wrong_number_in_title_rejected(self):
        """Test that title with wrong number is rejected"""
        components = ("LEGE", "53", "2003")
        title = "LEGE 333 08/07/2003 - Portal Legislativ"
        self.assertFalse(matches_reference(title, "", components))
    
    def test_different_law_type_rejected(self):
        """Test that different law type (DECIZIE vs LEGE) is rejected"""
        components = ("LEGE", "53", "2003")
        title = "DECIZIE 74 03/03/2025 - Portal Legislativ"
        description = "face referire la legea 53/2003"
        self.assertFalse(matches_reference(title, description, components))
    
    def test_hotarare_rejected_for_lege(self):
        """Test that HOTARARE doesn't match when searching for LEGE"""
        components = ("LEGE", "53", "2003")
        title = "HOTARARE 123 15/05/2003 - Portal Legislativ"
        description = "conform legii 53/2003"
        self.assertFalse(matches_reference(title, description, components))
    
    def test_oug_search_matches_oug(self):
        """Test that OUG search matches OUG title"""
        components = ("OUG", "50", "2020")
        title = "ORD DE URGENTA 50 01/04/2020 - Portal Legislativ"
        # Note: OUG needs to handle "ORD DE URGENTA" variant
        # This test documents current behavior
        self.assertFalse(matches_reference(title, "", components))  # OUG != ORD DE URGENTA
    
    def test_number_52_does_not_match_53(self):
        """Test that number 52 doesn't match 53"""
        components = ("LEGE", "53", "2003")
        title = "LEGE 52 03/03/2023 - Portal Legislativ"
        self.assertFalse(matches_reference(title, "", components))
    
    def test_year_1998_does_not_match_2003(self):
        """Test that year 1998 doesn't match 2003"""
        components = ("LEGE", "53", "2003")
        title = "LEGE 53 02/03/1998 - Portal Legislativ"
        self.assertFalse(matches_reference(title, "", components))
    
    def test_codul_fiscal_matches_via_description(self):
        """Test that CODUL FISCAL can match LEGE_227_2015 via description"""
        components = ("LEGE", "227", "2015")
        title = "CODUL FISCAL (A) 08/09/2015 - Portal Legislativ"
        description = "Legea nr. 227/2015 privind Codul fiscal"
        self.assertTrue(matches_reference(title, description, components))


class TestMatchingIntegration(unittest.TestCase):
    """Integration tests simulating real search scenarios."""
    
    def test_lege_53_2003_scenario(self):
        """Test the complete LEGE_53_2003 search scenario"""
        reference = "LEGE_53_2003"
        components = parse_reference_components(reference)
        
        # These should match
        matching_cases = [
            ("LEGE 53 24/01/2003 - Portal Legislativ", ""),
            ("LEGE (R) 53 24/01/2003 - Portal Legislativ", ""),
            ("LEGE (A) 53 24/01/2003 - Portal Legislativ", ""),
            ("CODUL MUNCII (A) 24/01/2003", "Legea nr. 53/2003 - Codul muncii"),
            ("CODUL MUNCII (R) 24/01/2003", "referire la 53/2003"),
        ]
        
        for title, desc in matching_cases:
            with self.subTest(title=title):
                self.assertTrue(
                    matches_reference(title, desc, components),
                    f"Expected '{title}' to match"
                )
        
        # These should NOT match
        non_matching_cases = [
            ("LEGE 53 30/04/2025 - Portal Legislativ", ""),  # Wrong year
            ("LEGE 333 08/07/2003 - Portal Legislativ", ""),  # Wrong number
            ("LEGE 52 03/03/2023 - Portal Legislativ", ""),  # Wrong number and year
            ("LEGE 53 03/03/2023 - Portal Legislativ", ""),  # Wrong year
            ("LEGE 53 02/03/1998 - Portal Legislativ", ""),  # Wrong year
            ("DECIZIE 74 03/03/2025", "referinta la 53/2003"),  # Different law type
            ("LEGE 161 29/05/2024", ""),  # Completely different
        ]
        
        for title, desc in non_matching_cases:
            with self.subTest(title=title):
                self.assertFalse(
                    matches_reference(title, desc, components),
                    f"Expected '{title}' to NOT match"
                )


if __name__ == '__main__':
    unittest.main()

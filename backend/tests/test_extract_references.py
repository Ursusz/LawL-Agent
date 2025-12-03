import unittest
from src.extract_references import extract_law_references


class TestExtractReferences(unittest.TestCase):

    def test_extract_references_nr_format(self):
        """Test extraction of references in 'nr. NUMBER/YEAR' format"""
        text = "Conform Legii nr. 53/2003 și Legii nr. 360/2023"
        refs = extract_law_references(text)
        
        self.assertIn('LEGE_53_2003', refs)
        self.assertIn('LEGE_360_2023', refs)
        self.assertEqual(len(refs), 2)

    def test_extract_references_din_format(self):
        """Test extraction of references in 'NUMBER din YEAR' format"""
        text = "Legea 120 din 2024 și Legea 287 din 2009"
        refs = extract_law_references(text)
        
        self.assertIn('LEGE_120_2024', refs)
        self.assertIn('LEGE_287_2009', refs)
        self.assertEqual(len(refs), 2)

    def test_extract_references_mixed_formats(self):
        """Test extraction of references in mixed formats (nr. and din)"""
        text = "Legea nr. 31/1990. Decizia nr. 99/100/2020. Legea 360 din 2023. Legea 120 din 2024."
        refs = extract_law_references(text)
        
        self.assertIn('LEGE_31_1990', refs)
        self.assertIn('DECIZIE_99_100_2020', refs)
        self.assertIn('LEGE_360_2023', refs)
        self.assertIn('LEGE_120_2024', refs)
        self.assertEqual(len(refs), 4)

    def test_extract_hotarare_references(self):
        """Test extraction of Hotărâre references"""
        text = "HG nr. 856/2020 și Hotărârea Guvernului 100 din 2023"
        refs = extract_law_references(text)
        
        self.assertIn('HG_856_2020', refs)
        self.assertIn('HG_100_2023', refs)  # Normalized to HG
        self.assertEqual(len(refs), 2)

    def test_extract_oug_references(self):
        """Test extraction of OUG references"""
        text = "OUG nr. 195/2002 și Ordonanța de urgență 117 din 2022"
        refs = extract_law_references(text)
        
        self.assertIn('OUG_195_2002', refs)
        self.assertIn('OUG_117_2022', refs)  # Normalized to OUG
        self.assertEqual(len(refs), 2)

    def test_deduplication(self):
        """Test that duplicate references are deduplicated"""
        text = "Legea nr. 360/2023 și Legea 360 din 2023"
        refs = extract_law_references(text)
        
        # Both should standardize to the same reference
        self.assertIn('LEGE_360_2023', refs)
        self.assertEqual(len(refs), 1)

    def test_no_references(self):
        """Test text with no legal references"""
        text = "This is just regular text without any legal references."
        refs = extract_law_references(text)
        
        self.assertEqual(len(refs), 0)


if __name__ == '__main__':
    unittest.main()

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure project root is in path to allow imports from backend.src
# Assuming this file is in backend/tests/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.src.web_scraping import web_scraper

class TestAnnexLogic(unittest.TestCase):

    def test_parent_text_extraction(self):
        # HTML structure: Parent with text "Parent Text" and a child
        # Note: data-list-text values should not have trailing dots for this test case based on previous findings
        html_content = """
        <html>
        <head><meta charset="utf-8"></head>
        <body>
            <div data-list-text="5.1">
                <p>Programul Idei</p>
                <p>Scop: Programul asigură finanțare pentru echipe de cercetare...</p>
                <p>Obiectivele programului:</p>
                <p>a) dezvoltarea cercetării exploratorii avansate trans- și inter- disciplinare;</p>
                <p>b) creșterea performanțelor calitative;</p>
                <p>c) atragerea și menținerea resurselor umane;</p>
                <p>d) creșterea gradului de utilizare a infrastructurii.</p>
            </div>
        </body>
        </html>
        """
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.content = html_content.encode('utf-8')
            mock_get.return_value = mock_response
            
            content = web_scraper.get_afis_page_content("http://fake.url")
            
            # Check if all parent text is present
            self.assertIn("5.1 Programul Idei", content)
            self.assertIn("Scop: Programul asigură finanțare", content)
            self.assertIn("Obiectivele programului:", content)
            # Check if all sub-items are present
            self.assertIn("a) dezvoltarea cercetării", content)
            self.assertIn("b) creșterea performanțelor", content)
            self.assertIn("c) atragerea și menținerea", content)
            self.assertIn("d) creșterea gradului de utilizare", content)

    def test_nested_list_text_extraction(self):
        """Test extraction with nested data-list-text items."""
        html_content = """
        <html>
        <head><meta charset="utf-8"></head>
        <body>
            <div data-list-text="5.1">
                <p>Programul Idei</p>
                <p>Scop: Programul asigură finanțare pentru echipe de cercetare...</p>
                <p>Obiectivele programului:</p>
                <div data-list-text="5.1.a)">
                    <p>dezvoltarea cercetării exploratorii avansate trans- și inter- disciplinare și a progreselor substanțiale la frontiera cunoașterii, cu elemente de noutate pe plan mondial;</p>
                </div>
                <div data-list-text="5.1.b)">
                    <p>creșterea performanțelor calitative și îmbunătățirea vizibilității internaționale a rezultatelor științifice românești;</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.content = html_content.encode('utf-8')
            mock_get.return_value = mock_response
            
            content = web_scraper.get_afis_page_content("http://fake.url")
            
            # Parent should have all its content (excluding children)
            self.assertIn("5.1 Programul Idei", content)
            self.assertIn("Scop: Programul asigură finanțare", content)
            self.assertIn("Obiectivele programului:", content)
            
            # Children should have full content
            self.assertIn("5.1.a)", content)
            self.assertIn("dezvoltarea cercetării exploratorii avansate", content)
            self.assertIn("5.1.b)", content)
            self.assertIn("creșterea performanțelor calitative", content)


    def test_annex_tagging_regex(self):
        # Test the regex substitution logic directly
        import re
        annex_content = "Articolul 1. Some text. ART. 2. Other text."
        tagged_content = re.sub(r'(Articolul|ART\.)', r'\1 (din Anexa)', annex_content)
        
        self.assertIn("Articolul (din Anexa) 1", tagged_content)
        self.assertIn("ART. (din Anexa) 2", tagged_content)

    def test_duplicate_data_list_text(self):
        """Test extraction when multiple items have the same data-list-text (one title, one content)."""
        html_content = """
        <html>
        <head><meta charset="utf-8"></head>
        <body>
            <!-- First occurrence: Title only (should be ignored in favor of the second) -->
            <div data-list-text="5.1">
                <p>Programul Idei</p>
            </div>
            
            <!-- Second occurrence: Full content (should be selected) -->
            <div data-list-text="5.1">
                <p>Programul Idei</p>
                <p>Scop: Programul asigură finanțare...</p>
                <p>Obiectivele programului: dezvoltarea cercetării...</p>
            </div>
        </body>
        </html>
        """
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.content = html_content.encode('utf-8')
            mock_get.return_value = mock_response
            
            content = web_scraper.get_afis_page_content("http://fake.url")
            
            # Should contain the full content
            self.assertIn("Scop: Programul asigură finanțare", content)
            self.assertIn("Obiectivele programului", content)
            
            # Should not duplicate the title excessively (though some duplication is expected due to structure)
            # The key is that we get the content from the second item

if __name__ == '__main__':
    unittest.main()

import unittest
import sys
import os

from src.web_scraping import web_scraper
from unittest.mock import patch, MagicMock

class TestE2EContentExtraction(unittest.TestCase):
    def test_parent_child_separation(self):
        """
        E2E test to verify that parent sections contain only their own content,
        not descendant content. Children should appear after separators.
        
        Expected output format:
        5. PROGRAME
        [only text in parent, not in any child]
        ----------------------------------------
        5.1 Programul Idei
        [full child content]
        ----------------------------------------
        5.2 ...
        """
        html_content = """
        <html>
        <head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"></head>
        <body>
            <!-- Parent 5. containing all descendant content embedded (short version) -->
            <div data-list-text="5.">
                <p>PROGRAME</p>
            </div>
            
            <!-- Parent 5. with full content including children (this is the "best" version) -->
            <div data-list-text="5.">
                <p>PROGRAME</p>
                <p>Intro text for programs section</p>
                <!-- Embedded child 5.1 content -->
                <div data-list-text="5.1">
                    <p>Programul Idei</p>
                    <p>Scop: Programul asigură finanțare...</p>
                </div>
                <!-- Embedded child 5.2 content -->
                <div data-list-text="5.2">
                    <p>Programul Resurse umane</p>
                    <p>Scop: Creșterea numărului...</p>
                </div>
            </div>
            
            <!-- Separate child 5.1 element (full content version) -->
            <div data-list-text="5.1">
                <p>Programul Idei</p>
                <p>Scop: Programul asigură finanțare...</p>
            </div>
            
            <!-- Separate child 5.2 element (full content version) -->
            <div data-list-text="5.2">
                <p>Programul Resurse umane</p>
                <p>Scop: Creșterea numărului...</p>
            </div>
        </body>
        </html>
        """
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.content = html_content.encode('utf-8')
            mock_get.return_value = mock_response
            
            content = web_scraper.get_afis_page_content("http://fake.url")
            
            # Split by separator
            sections = content.split('\n\n' + '-' * 40 + '\n\n')
            
            # Verify we have 3 sections (parent + 2 children)
            self.assertEqual(len(sections), 3, f"Expected 3 sections, got {len(sections)}")
            
            # Section 0: Parent "5. PROGRAME"
            parent_section = sections[0].strip()
            self.assertIn("5. PROGRAME", parent_section, "Parent section should contain '5. PROGRAME'")
            self.assertIn("Intro text for programs section", parent_section, 
                         "Parent section should contain its own intro text")
            self.assertNotIn("Programul Idei", parent_section, 
                            "Parent section should NOT contain child 5.1 content")
            self.assertNotIn("Programul Resurse umane", parent_section, 
                            "Parent section should NOT contain child 5.2 content")
            self.assertNotIn("Scop: Programul asigură finanțare", parent_section,
                            "Parent section should NOT contain child 5.1 detailed content")
            
            # Section 1: Child "5.1 Programul Idei"
            child1_section = sections[1].strip()
            self.assertIn("5.1", child1_section, "Child 1 section should contain '5.1'")
            self.assertIn("Programul Idei", child1_section, "Child 1 section should contain its title")
            self.assertIn("Scop: Programul asigură finanțare", child1_section,
                         "Child 1 section should contain its full content")
            self.assertNotIn("Programul Resurse umane", child1_section,
                            "Child 1 section should NOT contain child 5.2 content")
            
            # Section 2: Child "5.2 Programul Resurse umane"
            child2_section = sections[2].strip()
            self.assertIn("5.2", child2_section, "Child 2 section should contain '5.2'")
            self.assertIn("Programul Resurse umane", child2_section, "Child 2 section should contain its title")
            self.assertIn("Scop: Creșterea numărului", child2_section,
                         "Child 2 section should contain its full content")
            self.assertNotIn("Programul Idei", child2_section,
                            "Child 2 section should NOT contain child 5.1 content")

if __name__ == '__main__':
    unittest.main()

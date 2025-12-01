import unittest
import sys
import os

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.src.web_scraping import web_scraper
from unittest.mock import patch, MagicMock

class TestDuplication(unittest.TestCase):
    def test_no_duplication_parent_child(self):
        """
        Test that child content is not duplicated in the parent content.
        We'll use a mocked HTML structure that mimics the real issue:
        Parent contains the child text embedded, but we want to strip it out.
        """
        html_content = """
        <html>
        <body>
            <!-- Parent 5.2 containing child text embedded -->
            <div data-list-text="5.2">
                <p>Parent Title</p>
                <p>Parent Content</p>
                <!-- Embedded child content (no data-list-text or different one) -->
                <div>
                    <p>Child Title</p>
                    <p>Child Content</p>
                </div>
            </div>
            
            <!-- Child 5.2.1 defined separately -->
            <div data-list-text="5.2.1">
                <p>Child Title</p>
                <p>Child Content</p>
            </div>
        </body>
        </html>
        """
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.content = html_content.encode('utf-8')
            mock_get.return_value = mock_response
            
            content = web_scraper.get_afis_page_content("http://fake.url")
            
            # Parse the output to separate sections
            # We expect:
            # 5.2 Parent Title Parent Content
            # 5.2.1 Child Title Child Content
            
            # If duplication exists, 5.2 will contain "Child Title Child Content"
            
            # Simple check: split by lines
            lines = content.split('\n')
            
            # Find 5.2 section
            parent_text = ""
            child_text = ""
            current_section = None
            
            for line in lines:
                if "5.2" in line and "5.2.1" not in line:
                    current_section = "parent"
                elif "5.2.1" in line:
                    current_section = "child"
                
                if current_section == "parent":
                    parent_text += line
                elif current_section == "child":
                    child_text += line
            
            # Assert Child Content is NOT in Parent Text (except for the section header if any)
            # Note: "Child Title" might appear if it's part of the parent's flow, but "Child Content" should definitely be moved to the child section.
            # In our scraper logic, we remove the ENTIRE child text.
            
            self.assertNotIn("Child Content", parent_text, "Child content found duplicated in parent section")
            self.assertIn("Child Content", child_text, "Child content missing from child section")

if __name__ == '__main__':
    unittest.main()

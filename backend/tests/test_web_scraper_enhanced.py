"""Tests for enhanced web scraping functionality with linked documents."""
import unittest
from unittest.mock import MagicMock, patch, Mock
from lxml import html as lxml_html
from collections import Counter

# Import the functions we're testing
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from web_scraping.web_scraper import (
    get_afis_page_content,
    analyze_document_links,
    get_leg_just_ro_content
)


class TestEnhancedWebScraper(unittest.TestCase):
    """Test suite for enhanced web scraping with linked documents."""

    def test_analyze_document_links_with_repeated_links(self):
        """Test that repeated links are correctly identified."""
        # Create mock HTML with repeated links
        html_content = """
        <html>
            <body>
                <span class="S_ART_BDY">Short article text</span>
                <a href="~/../../Public/DetaliiDocumentAfis/260205">Link 1</a>
                <a href="~/../../Public/DetaliiDocumentAfis/260205">Link 2 (same)</a>
                <a href="~/../../Public/DetaliiDocumentAfis/47355">Different link</a>
            </body>
        </html>
        """
        tree = lxml_html.fromstring(html_content)
        
        result = analyze_document_links(tree)
        
        # Should find the repeated link
        self.assertEqual(len(result['repeated_links']), 1)
        self.assertIn('260205', result['repeated_links'][0])
        
        # Should count correctly
        self.assertEqual(result['link_counts']['https://legislatie.just.ro/Public/DetaliiDocumentAfis/260205'], 2)
        self.assertEqual(result['link_counts']['https://legislatie.just.ro/Public/DetaliiDocumentAfis/47355'], 1)

    def test_analyze_document_links_no_repeated_links(self):
        """Test when no links are repeated."""
        html_content = """
        <html>
            <body>
                <span class="S_ART_BDY">Article text</span>
                <a href="~/../../Public/DetaliiDocumentAfis/260205">Link 1</a>
                <a href="~/../../Public/DetaliiDocumentAfis/47355">Link 2</a>
            </body>
        </html>
        """
        tree = lxml_html.fromstring(html_content)
        
        result = analyze_document_links(tree)
        
        # Should find no repeated links
        self.assertEqual(len(result['repeated_links']), 0)

    def test_analyze_document_links_text_length(self):
        """Test that article and annex text lengths are correctly calculated."""
        html_content = """
        <html>
            <body>
                <span class="S_ART_BDY">This is article text with some content.</span>
                <span class="S_ART_BDY">More article content here.</span>
                <span class="S_ANX_BDY">Annex text.</span>
            </body>
        </html>
        """
        tree = lxml_html.fromstring(html_content)
        
        result = analyze_document_links(tree)
        
        # Check lengths are calculated
        self.assertGreater(result['article_text_length'], 0)
        self.assertGreater(result['annex_text_length'], 0)
        self.assertEqual(result['article_text_length'], len("This is article text with some content.More article content here."))
        self.assertEqual(result['annex_text_length'], len("Annex text."))

    @patch('web_scraping.web_scraper.requests.get')
    def test_get_afis_page_content_basic(self, mock_get):
        """Test basic content extraction from DetaliiDocumentAfis page."""
        # Mock response with typical structure
        html_content = """
        <html>
            <head><title>Test</title></head>
            <body>
                <nav>Navigation menu</nav>
                <div class="menu">Menu items</div>
                <div class="content">
                    <p>This is the actual content we want to extract.</p>
                    <p>More content here.</p>
                </div>
                <footer>Footer content</footer>
            </body>
        </html>
        """
        mock_response = Mock()
        mock_response.content = html_content.encode('utf-8')
        mock_get.return_value = mock_response
        
        result = get_afis_page_content('http://test.url')
        
        # Should extract content but not navigation/footer
        self.assertIn('actual content', result)
        self.assertNotIn('Navigation menu', result)
        self.assertNotIn('Footer content', result)

    @patch('web_scraping.web_scraper.requests.get')
    def test_get_afis_page_content_whitespace_cleanup(self, mock_get):
        """Test that excessive whitespace is cleaned up."""
        html_content = """
        <html>
            <body>
                <p>Line 1</p>
                
                
                <p>Line 2</p>
                <p>Line    with    spaces</p>
            </body>
        </html>
        """
        mock_response = Mock()
        mock_response.content = html_content.encode('utf-8')
        mock_get.return_value = mock_response
        
        result = get_afis_page_content('http://test.url')
        
        # Should not have excessive newlines or spaces
        self.assertNotIn('   ', result)  # No triple spaces
        self.assertNotIn('\n\n\n', result)  # No triple newlines

    @patch('web_scraping.web_scraper.cloud_file_management')
    @patch('web_scraping.web_scraper.requests.get')
    def test_get_leg_just_ro_content_short_doc_with_repeated_links(self, mock_get, mock_cloud):
        """Test HG 1188/2022 scenario: short doc with repeated links."""
        # Mock main document response (short content)
        main_html = """
        <html>
            <body>
                <span id="id_artA6_ttl">ARTICOL UNIC</span>
                <span class="S_ART_BDY">Se aprobă Planul național.</span>
                <span class="S_ANX_BDY">Anexă scurtă.</span>
                <a href="~/../../Public/DetaliiDocumentAfis/260205">Plan național</a>
                <a href="~/../../Public/DetaliiDocumentAfis/260205">Plan național (ref 2)</a>
                <a href="~/../../Public/DetaliiDocumentAfis/47355">Constituția</a>
            </body>
        </html>
        """
        
        # Mock linked document response (substantial content)
        linked_html = """
        <html>
            <body>
                <div>PLAN NAȚIONAL de cercetare, dezvoltare și inovare 2022-2027</div>
                <div>Lots of detailed content about the national plan...</div>
                <div>More content... """ + ("x" * 1000) + """</div>
            </body>
        </html>
        """
        
        # Setup mock responses
        def get_side_effect(url):
            mock_response = Mock()
            if 'DetaliiDocument/259888' in url:
                mock_response.content = main_html.encode('utf-8')
            elif 'DetaliiDocumentAfis/260205' in url:
                mock_response.content = linked_html.encode('utf-8')
            else:
                mock_response.content = b'<html><body></body></html>'
            return mock_response
        
        mock_get.side_effect = get_side_effect
        mock_cloud.save_file_in_cloud.return_value = 'test_file_id'
        
        # Execute
        result = get_leg_just_ro_content('https://legislatie.just.ro/Public/DetaliiDocument/259888', 'HG 1188 2022')
        
        # Verify file was saved
        self.assertEqual(result, 'test_file_id')
        
        # Verify the saved content includes linked document
        save_call_args = mock_cloud.save_file_in_cloud.call_args[0][0]
        with open(save_call_args, 'r') as f:
            saved_content = f.read()
        
        self.assertIn('ARTICOL UNIC', saved_content)
        self.assertIn('LINKED DOCUMENT', saved_content)
        self.assertIn('appears 2 times', saved_content)
        self.assertIn('260205', saved_content)

    @patch('web_scraping.web_scraper.cloud_file_management')
    @patch('web_scraping.web_scraper.requests.get')
    def test_get_leg_just_ro_content_long_doc_no_linked_fetch(self, mock_get, mock_cloud):
        """Test that long documents don't trigger linked document fetching."""
        # Mock main document response (long content - over 500 chars)
        long_content = "A" * 600  # 600 characters
        main_html = f"""
        <html>
            <body>
                <span id="id_artA6_ttl">ARTICOL 1</span>
                <span class="S_ART_BDY">{long_content}</span>
                <a href="~/../../Public/DetaliiDocumentAfis/260205">Link</a>
                <a href="~/../../Public/DetaliiDocumentAfis/260205">Link (repeated)</a>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.content = main_html.encode('utf-8')
        mock_get.return_value = mock_response
        mock_cloud.save_file_in_cloud.return_value = 'test_file_id'
        
        # Execute
        result = get_leg_just_ro_content('https://legislatie.just.ro/Public/DetaliiDocument/test', 'TEST_LAW')
        
        # Verify only one request was made (main document, no linked docs)
        self.assertEqual(mock_get.call_count, 1)
        
        # Verify saved content does NOT include linked document marker
        save_call_args = mock_cloud.save_file_in_cloud.call_args[0][0]
        with open(save_call_args, 'r') as f:
            saved_content = f.read()
        
        self.assertNotIn('LINKED DOCUMENT', saved_content)

    @patch('web_scraping.web_scraper.cloud_file_management')
    @patch('web_scraping.web_scraper.requests.get')
    def test_get_leg_just_ro_content_short_doc_no_repeated_links(self, mock_get, mock_cloud):
        """Test that short docs without repeated links don't fetch linked docs."""
        # Mock main document response (short but no repeated links)
        main_html = """
        <html>
            <body>
                <span id="id_artA6_ttl">ARTICOL 1</span>
                <span class="S_ART_BDY">Short text.</span>
                <a href="~/../../Public/DetaliiDocumentAfis/260205">Link 1</a>
                <a href="~/../../Public/DetaliiDocumentAfis/47355">Link 2 (different)</a>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.content = main_html.encode('utf-8')
        mock_get.return_value = mock_response
        mock_cloud.save_file_in_cloud.return_value = 'test_file_id'
        
        # Execute
        result = get_leg_just_ro_content('https://legislatie.just.ro/Public/DetaliiDocument/test', 'TEST_LAW')
        
        # Verify only one request was made (no linked docs fetched)
        self.assertEqual(mock_get.call_count, 1)

    @patch('web_scraping.web_scraper.cloud_file_management')
    @patch('web_scraping.web_scraper.requests.get')
    def test_get_leg_just_ro_content_linked_doc_fetch_error_handling(self, mock_get, mock_cloud):
        """Test that errors fetching linked documents are handled gracefully."""
        # Mock main document response (short with repeated links)
        main_html = """
        <html>
            <body>
                <span id="id_artA6_ttl">ARTICOL 1</span>
                <span class="S_ART_BDY">Short.</span>
                <a href="~/../../Public/DetaliiDocumentAfis/260205">Link</a>
                <a href="~/../../Public/DetaliiDocumentAfis/260205">Link (repeated)</a>
            </body>
        </html>
        """
        
        # Setup mock to succeed for main doc, fail for linked doc
        def get_side_effect(url):
            mock_response = Mock()
            if 'DetaliiDocument/test' in url:
                mock_response.content = main_html.encode('utf-8')
                return mock_response
            else:
                raise Exception("Network error")
        
        mock_get.side_effect = get_side_effect
        mock_cloud.save_file_in_cloud.return_value = 'test_file_id'
        
        # Execute - should not raise exception
        result = get_leg_just_ro_content('https://legislatie.just.ro/Public/DetaliiDocument/test', 'TEST_LAW')
        
        # Should still return successfully
        self.assertEqual(result, 'test_file_id')


if __name__ == '__main__':
    unittest.main()

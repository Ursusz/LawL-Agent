"""Integration tests for enhanced web scraping with real HTTP requests."""
import unittest
from unittest.mock import patch, Mock
import requests
from lxml import html as lxml_html
from collections import Counter
import re


def get_afis_page_content(url):
    """Extract content from a DetaliiDocumentAfis page."""
    response = requests.get(url)
    tree = lxml_html.fromstring(response.content)
    
    body = tree.xpath('//body')
    if not body:
        return ""
    
    for elem in tree.xpath("//nav | //header | //footer | //div[contains(@class, 'menu')] | //div[@id='menu']"):
        parent = elem.getparent()
        if parent is not None:
            parent.remove(elem)
    
    content_text = body[0].text_content().strip()
    content_text = re.sub(r'\n\s*\n', '\n\n', content_text)
    content_text = re.sub(r' +', ' ', content_text)
    
    return content_text


def analyze_document_links(tree):
    """Analyze a document page for linked documents."""
    all_links = tree.xpath('//a/@href')
    doc_links = [link for link in all_links if 'DetaliiDocumentAfis' in link]
    
    absolute_links = []
    for link in doc_links:
        if link.startswith('~'):
            link = link.replace('~/../../../Public/', 'https://legislatie.just.ro/Public/')
        elif not link.startswith('http'):
            link = 'https://legislatie.just.ro/Public/' + link.lstrip('/')
        absolute_links.append(link)
    
    link_counts = Counter(absolute_links)
    
    xpath_article_contents = "//span[@class='S_ART_BDY']"
    article_contents = tree.xpath(xpath_article_contents)
    article_text_length = sum(len(art.text_content()) for art in article_contents)
    
    xpath_annex_contents = "//span[@class='S_ANX_BDY']"
    annex_contents = tree.xpath(xpath_annex_contents)
    annex_text_length = sum(len(anx.text_content()) for anx in annex_contents)
    
    repeated_links = [link for link, count in link_counts.items() if count >= 2]
    
    return {
        'link_counts': link_counts,
        'article_text_length': article_text_length,
        'annex_text_length': annex_text_length,
        'repeated_links': repeated_links
    }


class TestWebScraperIntegration(unittest.TestCase):
    """Integration tests with real data from legislatie.just.ro."""

    def test_hg_1188_2022_real_data(self):
        """Test with real HG 1188/2022 - the example from requirements."""
        url = "https://legislatie.just.ro/Public/DetaliiDocument/259888"
        
        response = requests.get(url)
        tree = lxml_html.fromstring(response.content)
        
        # Analyze the document
        analysis = analyze_document_links(tree)
        
        # Verify it's a short document
        total_length = analysis['article_text_length'] + analysis['annex_text_length']
        self.assertLess(total_length, 2000, "HG 1188/2022 should be a short document")
        
        # Verify it has repeated links
        self.assertGreater(len(analysis['repeated_links']), 0, "Should have at least one repeated link")
        
        # Verify the specific link 260205 appears twice
        link_260205 = 'https://legislatie.just.ro/Public/DetaliiDocumentAfis/260205'
        self.assertIn(link_260205, analysis['repeated_links'], "Link 260205 should be repeated")
        self.assertEqual(analysis['link_counts'][link_260205], 2, "Link 260205 should appear exactly twice")
        
        print(f"\n✓ HG 1188/2022 analysis:")
        print(f"  - Article text: {analysis['article_text_length']} chars")
        print(f"  - Annex text: {analysis['annex_text_length']} chars")
        print(f"  - Total: {total_length} chars")
        print(f"  - Repeated links: {len(analysis['repeated_links'])}")

    def test_fetch_linked_document_260205(self):
        """Test fetching the linked document 260205 (Plan național)."""
        url = "https://legislatie.just.ro/Public/DetaliiDocumentAfis/260205"
        
        content = get_afis_page_content(url)
        
        # Verify substantial content was extracted
        self.assertGreater(len(content), 10000, "Linked document should have substantial content")
        
        # Verify it contains expected keywords
        self.assertIn("2022", content, "Should contain year 2022")
        self.assertIn("2027", content, "Should contain year 2027")
        
        print(f"\n✓ Linked document 260205:")
        print(f"  - Content length: {len(content)} chars")
        print(f"  - Preview: {content[:100]}...")

    def test_analyze_document_links_unit(self):
        """Unit test for analyze_document_links with mock HTML."""
        html_content = """
        <html>
            <body>
                <span class="S_ART_BDY">Article text here</span>
                <span class="S_ANX_BDY">Annex text</span>
                <a href="~/../../../Public/DetaliiDocumentAfis/260205">Link 1</a>
                <a href="~/../../../Public/DetaliiDocumentAfis/260205">Link 2</a>
                <a href="~/../../../Public/DetaliiDocumentAfis/47355">Different link</a>
            </body>
        </html>
        """
        tree = lxml_html.fromstring(html_content)
        
        result = analyze_document_links(tree)
        
        # Verify repeated links detection
        self.assertEqual(len(result['repeated_links']), 1)
        self.assertIn('260205', result['repeated_links'][0])
        
        # Verify link counts
        self.assertEqual(result['link_counts']['https://legislatie.just.ro/Public/DetaliiDocumentAfis/260205'], 2)
        self.assertEqual(result['link_counts']['https://legislatie.just.ro/Public/DetaliiDocumentAfis/47355'], 1)
        
        # Verify text lengths
        self.assertGreater(result['article_text_length'], 0)
        self.assertGreater(result['annex_text_length'], 0)

    def test_get_afis_page_content_unit(self):
        """Unit test for get_afis_page_content with mock response."""
        html_content = """
        <html>
            <body>
                <nav>Navigation</nav>
                <div class="menu">Menu</div>
                <div class="content">
                    <p>Important content line 1</p>
                    <p>Important content line 2</p>
                </div>
                <footer>Footer</footer>
            </body>
        </html>
        """
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.content = html_content.encode('utf-8')
            mock_get.return_value = mock_response
            
            result = get_afis_page_content('http://test.url')
            
            # Should include content
            self.assertIn('Important content', result)
            
            # Should exclude navigation and footer
            self.assertNotIn('Navigation', result)
            self.assertNotIn('Footer', result)

    def test_short_document_threshold(self):
        """Test that the 2000 character threshold works correctly."""
        # Test with short document
        short_html = """
        <html>
            <body>
                <span class="S_ART_BDY">Short text</span>
                <a href="~/../../../Public/DetaliiDocumentAfis/260205">Link</a>
                <a href="~/../../../Public/DetaliiDocumentAfis/260205">Link</a>
            </body>
        </html>
        """
        tree = lxml_html.fromstring(short_html)
        analysis = analyze_document_links(tree)
        total_length = analysis['article_text_length'] + analysis['annex_text_length']
        
        # Should trigger linked document fetching
        should_fetch = total_length < 2000 and len(analysis['repeated_links']) > 0
        self.assertTrue(should_fetch, "Short document with repeated links should trigger fetching")
        
        # Test with long document
        long_text = "A" * 2500
        long_html = f"""
        <html>
            <body>
                <span class="S_ART_BDY">{long_text}</span>
                <a href="~/../../../Public/DetaliiDocumentAfis/260205">Link</a>
                <a href="~/../../../Public/DetaliiDocumentAfis/260205">Link</a>
            </body>
        </html>
        """
        tree = lxml_html.fromstring(long_html)
        analysis = analyze_document_links(tree)
        total_length = analysis['article_text_length'] + analysis['annex_text_length']
        
        # Should NOT trigger linked document fetching
        should_fetch = total_length < 2000 and len(analysis['repeated_links']) > 0
        self.assertFalse(should_fetch, "Long document should not trigger fetching even with repeated links")


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)

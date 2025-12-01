"""
Demonstration of enhanced web scraping with HG 1188/2022.

This script shows how the enhanced scraper automatically fetches
linked documents when the main document is short.
"""
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


def demo_enhanced_scraping():
    """Demonstrate the enhanced scraping with HG 1188/2022."""
    print("=" * 70)
    print("DEMONSTRATION: Enhanced Web Scraping")
    print("Example: HG 1188/2022")
    print("=" * 70)
    
    url = "https://legislatie.just.ro/Public/DetaliiDocument/259888"
    
    print(f"\n1. Fetching main document: {url}")
    response = requests.get(url)
    tree = lxml_html.fromstring(response.content)
    
    # Extract main content
    xpath_article_titles = "//*[starts-with(@id, 'id_art') and substring(@id, string-length(@id) - 2, 3) = 'ttl' and not(ancestor::*[contains(@class, 'S_ANX_BDY')])]"
    article_titles = tree.xpath(xpath_article_titles)
    
    xpath_article_contents = "//span[@class='S_ART_BDY']"
    article_contents = tree.xpath(xpath_article_contents)
    
    main_content = ""
    for index in range(len(article_titles)):
        main_content += article_titles[index].text_content() + "\n"
        main_content += article_contents[index].text_content().replace("...", "") + "\n"
    
    print(f"\n2. Main document content ({len(main_content)} chars):")
    print("-" * 70)
    print(main_content[:300] + "...")
    print("-" * 70)
    
    # Analyze links
    print("\n3. Analyzing document links...")
    analysis = analyze_document_links(tree)
    
    print(f"   - Article text: {analysis['article_text_length']} chars")
    print(f"   - Annex text: {analysis['annex_text_length']} chars")
    print(f"   - Total: {analysis['article_text_length'] + analysis['annex_text_length']} chars")
    print(f"\n   All linked documents:")
    for link, count in analysis['link_counts'].most_common():
        marker = " ← REPEATED!" if count >= 2 else ""
        print(f"   - {count}x: {link}{marker}")
    
    # Check if we should fetch linked docs
    total_length = analysis['article_text_length'] + analysis['annex_text_length']
    should_fetch = total_length < 500 and len(analysis['repeated_links']) > 0
    
    print(f"\n4. Decision: Should fetch linked documents?")
    print(f"   - Document is short (< 500 chars): {total_length < 500}")
    print(f"   - Has repeated links: {len(analysis['repeated_links']) > 0}")
    print(f"   - RESULT: {'YES ✓' if should_fetch else 'NO ✗'}")
    
    if should_fetch:
        print(f"\n5. Fetching linked documents...")
        for linked_url in analysis['repeated_links']:
            link_count = analysis['link_counts'][linked_url]
            print(f"\n   Fetching: {linked_url}")
            print(f"   (appears {link_count} times)")
            
            linked_content = get_afis_page_content(linked_url)
            print(f"   ✓ Extracted {len(linked_content):,} characters")
            print(f"   Preview: {linked_content[:150]}...")
        
        final_length = len(main_content) + sum(
            len(get_afis_page_content(link)) for link in analysis['repeated_links']
        )
        print(f"\n6. FINAL RESULT:")
        print(f"   - Original content: {len(main_content):,} chars")
        print(f"   - With linked docs: {final_length:,} chars")
        print(f"   - Improvement: {final_length / len(main_content):.1f}x more content!")
    
    print("\n" + "=" * 70)
    print("Demonstration complete!")
    print("=" * 70)


if __name__ == '__main__':
    demo_enhanced_scraping()

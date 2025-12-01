import requests
from lxml import html
import re, os
from collections import Counter
from ..utilities import parse_law_title, standardize_law_title, cloud_file_management

# Threshold for determining if a document is "short" and should fetch linked docs
SHORT_DOCUMENT_THRESHOLD = 2000

def get_afis_page_content(url):
  """
  Extract content from a DetaliiDocumentAfis page.
  Attempts to extract articles first (like main docs), falls back to raw text.
  """
  response = requests.get(url)
  tree = html.fromstring(response.content)
  
  # Try to extract articles first (same as main documents)
  xpath_article_titles = "//*[starts-with(@id, 'id_art') and substring(@id, string-length(@id) - 2, 3) = 'ttl' and not(ancestor::*[contains(@class, 'S_ANX_BDY')])]"
  article_titles = tree.xpath(xpath_article_titles)
  
  xpath_article_contents = "//span[@class='S_ART_BDY']"
  article_contents = tree.xpath(xpath_article_contents)
  
  # If articles found, extract them (same format as main docs)
  if article_titles and article_contents and len(article_titles) == len(article_contents):
    content_text = ""
    for index in range(len(article_titles)):
      content_text += article_titles[index].text_content() + "\n"
      content_text += article_contents[index].text_content().replace("...", "") + "\n"
    return content_text
  
  # Fallback: extract using data-list-text chunking (for structured documents)
  list_items = tree.xpath('//*[@data-list-text]')
  if list_items:
    content_text = ""
    processed_parents = set()  # Track parent items we've already processed
    
    for item in list_items:
      list_text = item.get('data-list-text', '')
      
      # Skip if this is a nested item (contains a dot beyond first level)
      # e.g., skip 5.2.1 but process 5.2
      if list_text.count('.') > 1:
        continue
      
      # Check if this item has children (one level of nesting)
      children = tree.xpath(f'//*[@data-list-text and starts-with(@data-list-text, "{list_text}.")]')
      
      # Get item content (exclude nested children content)
      item_content = item.text_content().strip()
      
      # If has children, extract only direct text (not nested)
      if children:
        # Mark as processed
        processed_parents.add(list_text)
        
        # Add parent header
        content_text += f"{list_text} "
        # Get direct text of parent (first line usually)
        lines = item_content.split('\n')
        content_text += lines[0].strip() + "\n"
        
        # Add children (one level deep only)
        for child in children:
          child_list_text = child.get('data-list-text', '')
          # Only process direct children (e.g., 5.1, 5.2, not 5.2.1)
          if child_list_text.count('.') == 1:
            child_content = child.text_content().strip()
            child_lines = child_content.split('\n')
            content_text += f"  {child_list_text} {child_lines[0].strip()}\n"
      else:
        # No children, add as-is (if not already processed as parent)
        if list_text not in processed_parents:
          lines = item_content.split('\n')
          content_text += f"{list_text} {lines[0].strip()}\n"
    
    if content_text:
      return content_text
  
  # Final fallback: raw text extraction
  body = tree.xpath('//body')
  if not body:
    return ""
  
  # Remove navigation, header, footer elements
  for elem in tree.xpath("//nav | //header | //footer | //div[contains(@class, 'menu')] | //div[@id='menu']"):
    parent = elem.getparent()
    if parent is not None:
      parent.remove(elem)
  
  content_text = body[0].text_content().strip()
  
  # Clean up the text - remove excessive whitespace
  content_text = re.sub(r'\n\s*\n', '\n\n', content_text)
  content_text = re.sub(r' +', ' ', content_text)
  
  return content_text


def analyze_document_links(tree):
  """
  Analyze a document page for linked documents.
  Returns link frequency data and text lengths.
  """
  # Find all links to other documents
  all_links = tree.xpath('//a/@href')
  # Filter for DetaliiDocumentAfis links (supplementary documents)
  doc_links = [link for link in all_links if 'DetaliiDocumentAfis' in link]
  
  # Convert relative URLs to absolute
  absolute_links = []
  for link in doc_links:
    if link.startswith('~'):
      link = link.replace('~/../../../Public/', 'https://legislatie.just.ro/Public/')
    elif not link.startswith('http'):
      link = 'https://legislatie.just.ro/Public/' + link.lstrip('/')
    absolute_links.append(link)
  
  # Count occurrences
  link_counts = Counter(absolute_links)
  
  # Check the text content length of main document
  xpath_article_contents = "//span[@class='S_ART_BDY']"
  article_contents = tree.xpath(xpath_article_contents)
  article_text_length = sum(len(art.text_content()) for art in article_contents)
  
  # Check for annexes
  xpath_annex_contents = "//span[@class='S_ANX_BDY']"
  annex_contents = tree.xpath(xpath_annex_contents)
  annex_text_length = sum(len(anx.text_content()) for anx in annex_contents)
  
  # Find links that appear multiple times (2+)
  repeated_links = [link for link, count in link_counts.items() if count >= 2]
  
  # Extract annex links (from S_ANX_BDY sections)
  annex_section = tree.xpath("//span[@class='S_ANX_BDY']")
  annex_links = []
  if annex_section:
    for anx in annex_section:
      anx_links = anx.xpath(".//a[contains(@href, 'DetaliiDocumentAfis')]/@href")
      for link in anx_links:
        if link.startswith('~'):
          link = link.replace('~/../../../Public/', 'https://legislatie.just.ro/Public/')
        elif not link.startswith('http'):
          link = 'https://legislatie.just.ro/Public/' + link.lstrip('/')
        annex_links.append(link)
  
  return {
    'link_counts': link_counts,
    'article_text_length': article_text_length,
    'annex_text_length': annex_text_length,
    'repeated_links': repeated_links,
    'annex_links': annex_links
  }


def get_leg_just_ro_content(url, reference):
  response = requests.get(url)
  tree = html.fromstring(response.content)

  # Articol 1, Articol 2, Articol 3, ... // ART. 1, ART. 2, ...
  xpath_article_titles = "//*[starts-with(@id, 'id_art') and substring(@id, string-length(@id) - 2, 3) = 'ttl' and not(ancestor::*[contains(@class, 'S_ANX_BDY')])]"
  article_titles = tree.xpath(xpath_article_titles)

  # Continutul articolelor
  xpath_article_contents = "//span[@class='S_ART_BDY']"
  article_contents = tree.xpath(xpath_article_contents)

  # Concatenez TITLU_ARTICOL + CONTENT_ARTICOL
  law = ""
  for index in range(len(article_titles)):
    law += article_titles[index].text_content() + "\n" + article_contents[index].text_content().replace("...", "") + "\n"

  # Analyze for linked documents if main document is short
  link_analysis = analyze_document_links(tree)
  total_main_length = link_analysis['article_text_length'] + link_analysis['annex_text_length']
  
  # If document is short and has repeated links, fetch them
  if total_main_length < SHORT_DOCUMENT_THRESHOLD and link_analysis['repeated_links']:
    print(f"Main document is short ({total_main_length} chars), fetching linked documents...")
    
    for linked_url in link_analysis['repeated_links']:
      link_count = link_analysis['link_counts'][linked_url]
      print(f"Fetching linked document (appears {link_count} times): {linked_url}")
      
      # Extract document ID from URL for caching
      doc_id = linked_url.split('/')[-1]
      cache_filename = f"linked_{doc_id}.txt"
      
      # Check cache first
      cached_file_id = cloud_file_management.search_file_in_cloud(cache_filename)
      if cached_file_id:
        print(f"Found in cache: {cache_filename}")
        cached_content = cloud_file_management.download_file_content(cached_file_id)
        lines = cached_content.splitlines()
        linked_content = '\n'.join(lines[1:]) if len(lines) > 1 else cached_content
      else:
        try:
          linked_content = get_afis_page_content(linked_url)
          if linked_content and len(linked_content) > 100:
            # Save to cache
            cache_path = os.path.join("../TMP", cache_filename)
            with open(cache_path, "w") as f:
              f.write(linked_url + "\n")
              f.write(linked_content)
            cloud_file_management.save_file_in_cloud(cache_path)
            print(f"Cached linked document as {cache_filename}")
        except Exception as e:
          print(f"Error fetching linked document {linked_url}: {e}")
          linked_content = None
      
      if linked_content and len(linked_content) > 100:
        law += f"\n\n{'='*60}\n"
        law += f"LINKED DOCUMENT (appears {link_count} times):\n"
        law += f"Source: {linked_url}\n"
        law += f"{'='*60}\n\n"
        law += linked_content
        print(f"Added {len(linked_content)} characters from linked document")
  
  # Cautiously fetch annex links only if:
  # 1. No repeated links were found (prefer repeated links)
  # 2. Annexes themselves are short (< 500 chars)
  # 3. Main document is still short overall
  if (not link_analysis['repeated_links'] and 
      link_analysis['annex_links'] and 
      link_analysis['annex_text_length'] < 500 and
      total_main_length < SHORT_DOCUMENT_THRESHOLD):
    print(f"No repeated links found, checking annex links (annex is short: {link_analysis['annex_text_length']} chars)...")
    
    for annex_url in link_analysis['annex_links'][:1]:  # Only fetch first annex link
      doc_id = annex_url.split('/')[-1]
      cache_filename = f"annex_{doc_id}.txt"
      
      cached_file_id = cloud_file_management.search_file_in_cloud(cache_filename)
      if cached_file_id:
        print(f"Found in cache: {cache_filename}")
        cached_content = cloud_file_management.download_file_content(cached_file_id)
        lines = cached_content.splitlines()
        annex_content = '\n'.join(lines[1:]) if len(lines) > 1 else cached_content
      else:
        try:
          annex_content = get_afis_page_content(annex_url)
          if annex_content and len(annex_content) > 100:
            cache_path = os.path.join("../TMP", cache_filename)
            with open(cache_path, "w") as f:
              f.write(annex_url + "\n")
              f.write(annex_content)
            cloud_file_management.save_file_in_cloud(cache_path)
            print(f"Cached annex document as {cache_filename}")
        except Exception as e:
          print(f"Error fetching annex document {annex_url}: {e}")
          annex_content = None
      
      if annex_content and len(annex_content) > 100:
        law += f"\n\n{'='*60}\n"
        law += f"ANNEX DOCUMENT:\n"
        law += f"Source: {annex_url}\n"
        law += f"{'='*60}\n\n"
        law += annex_content
        print(f"Added {len(annex_content)} characters from annex document")
        break  # Only add one annex document


  folder = "../TMP"
  if not os.path.exists(folder):
      os.makedirs(folder)

  file_name = f"{reference}.txt"
    
  file_saving_location = os.path.join(folder, file_name)
  with open(file_saving_location, "w") as file:
    file.write(url + "\n")
    file.write(law)
  return cloud_file_management.save_file_in_cloud(file_saving_location)

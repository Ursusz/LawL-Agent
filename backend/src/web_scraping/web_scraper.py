import requests
from lxml import html
import re, os
from collections import Counter
from ..utilities import parse_law_title, standardize_law_title, cloud_file_management

# Threshold for determining if a document is "short" and should fetch linked docs
SHORT_DOCUMENT_THRESHOLD = 2000

def extract_text_with_spacing(element):
  """Extract text preserving layout (newlines for br and block elements)."""
  text = []
  def _process(node):
    if node.text:
      text.append(node.text)
    for child in node:
      if child.tag == 'br':
        text.append('\n')
      elif child.tag in ['p', 'div', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'tr']:
        text.append('\n')
        _process(child)
        text.append('\n')
      else:
        _process(child)
      if child.tail:
        text.append(child.tail)
  _process(element)
  
  raw_text = "".join(text)
  
  import re
  # Collapse horizontal whitespace (spaces, tabs) to single space
  raw_text = re.sub(r'[ \t]+', ' ', raw_text)
  # Collapse multiple newlines to max 2
  return re.sub(r'\n{3,}', '\n\n', raw_text).strip()

def get_afis_page_content(url):
  response = requests.get(url)
  tree = html.fromstring(response.content)
  
  body = tree.xpath('//body')
  if not body:
    return ""
  
  # Remove navigation, header, footer, style, and script elements
  for elem in tree.xpath("//nav | //header | //footer | //div[contains(@class, 'menu')] | //div[@id='menu'] | //style | //script"):
    parent = elem.getparent()
    if parent is not None:
      parent.remove(elem)
  
  # 1. Try to find article structure (S_ART_BDY)
  xpath_article_titles = "//*[starts-with(@id, 'id_art') and substring(@id, string-length(@id) - 2, 3) = 'ttl' and not(ancestor::*[contains(@class, 'S_ANX_BDY')])]"
  article_titles = tree.xpath(xpath_article_titles)
  
  xpath_article_contents = "//span[@class='S_ART_BDY']"
  article_contents = tree.xpath(xpath_article_contents)
  
  if article_titles and article_contents and len(article_titles) == len(article_contents):
    law = ""
    for index in range(len(article_titles)):
      law += article_titles[index].text_content() + "\n" + article_contents[index].text_content().replace("...", "") + "\n"
    return law

  # 2. Fallback: Structured chunking using data-list-text
  list_items = tree.xpath('//*[@data-list-text]')
  if list_items:
    content_text = ""
    
    # Group items by data-list-text to handle duplicates
    # The website sometimes has multiple elements with the same data-list-text,
    # where one is just a title and another has the full content.
    items_by_id = {}
    for item in list_items:
      list_text = item.get('data-list-text', '')
      if not list_text:
        continue
        
      # If we already have this ID, check if the new one has more content
      if list_text in items_by_id:
        current_len = len(items_by_id[list_text].text_content().strip())
        new_len = len(item.text_content().strip())
        if new_len > current_len:
          items_by_id[list_text] = item
      else:
        items_by_id[list_text] = item
    
    # Get the best unique items
    unique_items = list(items_by_id.values())
    
    # Sort by position in document to maintain order (approximation)
    # We can't easily sort by document position after grouping, so we'll iterate 
    # through original list and process if it matches our "best" item
    
    processed_ids = set()
    
    def process_item_with_children(item, tree, indent_level=0):
      """Recursively process an item and its children."""
      list_text = item.get('data-list-text', '')
      
      # Skip if already processed
      if list_text in processed_ids:
        return ""
      
      processed_ids.add(list_text)
      
      # Check for children - look in our unique items map
      children = []
      for other_id, other_item in items_by_id.items():
        if other_id != list_text and other_id.startswith(list_text + "."):
            # Verify it's a direct child or close descendant we want to include
            # For 5.1, we want 5.1.a), but maybe not 5.1.1 if that's a different branch
            # The simple startswith check is usually good enough for this structure
            children.append(other_item)
            
      # Sort children by their ID to ensure correct order (e.g. 5.1.a before 5.1.b)
      # We need a smart sort that handles numbers and letters
      def sort_key(child):
          key = child.get('data-list-text', '')
          # Try to normalize for sorting
          return key
      
      children.sort(key=sort_key)
      
      # Build output for this item
      indent = "  " * indent_level
      
      if children:
        # Parent node: extract text and remove all descendant text
        # Simple string-based approach: extract parent text, then remove each descendant's text
        
        # Extract full text from parent
        parent_text = extract_text_with_spacing(item).strip()
        
        # Get all descendant IDs
        descendant_ids = []
        for other_id in items_by_id.keys():
            if other_id != list_text:
                if list_text.endswith("."):
                    is_descendant = other_id.startswith(list_text) and other_id != list_text
                else:
                    is_descendant = other_id.startswith(list_text + ".")
                
                if is_descendant:
                    descendant_ids.append(other_id)
        
        # Sort by depth (deepest first) to avoid partial replacements
        descendant_ids.sort(key=lambda x: x.count('.'), reverse=True)
        
        # Remove each descendant's text from parent text
        for desc_id in descendant_ids:
            if desc_id in items_by_id:
                desc_text = extract_text_with_spacing(items_by_id[desc_id]).strip()
                if desc_text and desc_text in parent_text:
                    parent_text = parent_text.replace(desc_text, "").strip()
        
        item_content = parent_text
        
        result = f"{indent}{list_text} {item_content}\n"
        
        # Process children recursively
        for child in children:
            # Only process if it's a direct child in the hierarchy we haven't seen
            child_id = child.get('data-list-text', '')
            if child_id not in processed_ids:
                 result += process_item_with_children(child, tree, indent_level + 1)
      else:
        # Leaf node: extract ALL content
        import copy
        item_clone = copy.deepcopy(item)
        item_content = extract_text_with_spacing(item_clone).strip()
        result = f"{indent}{list_text} {item_content}\n"
      
      return result
    
    # Process top-level items (those that are not children of other items in our set)
    # An item is top-level if no other item in items_by_id is its parent
    sorted_ids = sorted(items_by_id.keys())
    
    for list_text in sorted_ids:
      if list_text in processed_ids:
        continue
        
      # Check if this is a child of another item in our set
      is_child = False
      for other_text in items_by_id.keys():
        if other_text != list_text and list_text.startswith(other_text + "."):
          is_child = True
          break
      
      if not is_child:
        chunk = process_item_with_children(items_by_id[list_text], tree)
        if content_text and chunk:
          if chunk.split(" ", 1)[1][0:100] in content_text:
            clean_chunk = re.sub(r"^\s*[0-9]+[0-9\.]* ", "\n", chunk.strip(), flags=re.MULTILINE)
            clean_chunk = re.sub(r"^\s*[a-z]+\) ", "", clean_chunk, flags=re.MULTILINE).strip()
            content_text = content_text.replace(clean_chunk, "")
            content_text += "\n\n" + "-" * 40 + "\n\n"
        content_text += chunk
    
    if content_text:
      # Clean up the text - remove excessive whitespace
      content_text = re.sub(r'\n\s*\n', '\n\n', content_text)
      content_text = re.sub(r' +', ' ', content_text)
      return content_text
  
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
        if cached_content:
          lines = cached_content.splitlines()
          linked_content = '\n'.join(lines[1:]) if len(lines) > 1 else cached_content
        else:
          linked_content = None
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
        if cached_content:
          lines = cached_content.splitlines()
          annex_content = '\n'.join(lines[1:]) if len(lines) > 1 else cached_content
        else:
          annex_content = None
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
        # Tag annex articles
        annex_content = re.sub(r'(Articolul|ART\.)', r'\1 (din Anexa)', annex_content)
        
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

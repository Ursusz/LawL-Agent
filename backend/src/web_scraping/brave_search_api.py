import requests
from .. import config
import os
from . import web_scraper
import json
import re


brave_api_key = os.getenv("BRAVE_SEARCH_API_KEY")

TRUSTED_DOMAINS = [
    'legislatie.just.ro'
]

def extract_url_id(url):
  """Extract the ID from a legislatie.just.ro URL.
  
  URLs are like:
  - https://legislatie.just.ro/Public/DetaliiDocument/41625
  - https://legislatie.just.ro/Public/DetaliiDocumentAfis/128646
  
  Returns the ID as an integer, or 0 if not found.
  """
  match = re.search(r'/(\d+)/?$', url)
  if match:
    return int(match.group(1))
  return 0

def parse_reference_components(reference):
  """Parse a normalized reference into its components.
  
  Examples:
  - "LEGE_53_2003" -> ("LEGE", "53", "2003")
  - "DECIZIE_99_100_2020" -> ("DECIZIE", "99_100", "2020")
  - "HG_123_2020" -> ("HG", "123", "2020")
  - "Regulamentul_UE_2016_679" -> ("REGULAMENTUL", "UE_679", "2016")
  
  Returns (law_type, number, year) or None if parsing fails.
  """
  parts = reference.split('_')
  if len(parts) < 3:
    return None
  
  # Law type is the first part
  law_type = parts[0]
  
  # Find the year (should be a 4-digit number anywhere in the parts)
  year = None
  year_index = -1
  for i, part in enumerate(parts):
    if part.isdigit() and len(part) == 4:
      year = part
      year_index = i
      break
  
  if not year:
    return None
  
  # Number is everything except the law type and year
  number_parts = [p for i, p in enumerate(parts[1:], start=1) if i != year_index]
  number = '_'.join(number_parts)
  
  if not number:
    return None
  
  return (law_type, number, year)

def matches_numeric_ids(text, reference_components):
  """Check if the numeric IDs (number and year) appear in the text.
  
  This is used for partial matching in descriptions where the law type might
  differ but the numeric identifiers are the same (e.g., searching for "LEGE_53_2003"
  but finding "CODUL MUNCII" with "53/2003" in the description).
  
  Args:
    text: Text to search in (title or description)
    reference_components: Tuple of (law_type, number, year)
  
  Returns True if both number and year are found, False otherwise.
  """
  if not reference_components:
    return False
  
  law_type, number, year = reference_components
  
  # Normalize text to uppercase for comparison
  text_upper = text.upper()
  
  # Check if the number appears in the text as a complete word
  # Handle cases like "99/100" or "99 100" for references like "DECIZIE_99_100_2020"
  # Use word boundaries to prevent "53" from matching "153" or "533"
  number_variants = [
    number,  # "53" or "99_100"
    number.replace('_', '/'),  # "99/100"
    number.replace('_', ' '),  # "99 100"
  ]
  
  number_found = False
  for num_variant in number_variants:
    # Use word boundary to match complete numbers only
    number_pattern = r'\b' + re.escape(num_variant) + r'\b'
    if re.search(number_pattern, text_upper):
      number_found = True
      break
  
  if not number_found:
    return False
  
  # Check if the year appears as a complete word/number (not as substring)
  # Use word boundaries to ensure "2003" doesn't match "2025"
  year_pattern = r'\b' + re.escape(year) + r'\b'
  if not re.search(year_pattern, text_upper):
    return False
  
  return True

def matches_reference(title, description, reference_components):
  """Check if a search result matches the reference components.
  
  First checks if the title fully matches (law type + number + year).
  If the title identifies a different law (same type but wrong number/year), reject it.
  If the title contains a different law type entirely, reject it.
  Only allows description fallback for titles that don't identify a specific numbered law.
  
  Args:
    title: Search result title like "LEGE 53 24/01/2003" or "CODUL MUNCII"
    description: Search result description
    reference_components: Tuple of (law_type, number, year)
  
  Returns True if there's a match, False otherwise.
  """
  if not reference_components:
    return False
  
  law_type, number, year = reference_components
  
  # Normalize title to uppercase for comparison
  title_upper = title.upper()
  
  # List of known law types - if title contains one of these that ISN'T our target, reject it
  # Note: 'CODUL' is NOT included because it's a naming format (e.g., "Codul Muncii" = LEGE 53/2003)
  KNOWN_LAW_TYPES = [
    'LEGE', 'HG', 'OG', 'OUG', 'DECIZIE', 'ORDIN', 'HOTARARE', 
    'ORDONANTA', 'REGULAMENT', 'DIRECTIVA', 'DECRET'
  ]
  
  # Check if title contains a different law type - if so, reject this result
  for known_type in KNOWN_LAW_TYPES:
    if known_type in title_upper and known_type != law_type:
      # Title has a different law type - this is a completely different document
      # Exception: if our law_type is also in the title, continue checking
      if law_type not in title_upper:
        return False
  
  # Check if law type is in title
  law_type_in_title = law_type in title_upper
  
  # Check if number is in title (with word boundaries)
  number_variants = [
    number,  # "53" or "99_100"
    number.replace('_', '/'),  # "99/100"
    number.replace('_', ' '),  # "99 100"
  ]
  
  number_in_title = False
  for num_variant in number_variants:
    number_pattern = r'\b' + re.escape(num_variant) + r'\b'
    if re.search(number_pattern, title_upper):
      number_in_title = True
      break
  
  # Check if year is in title (with word boundaries)
  year_pattern = r'\b' + re.escape(year) + r'\b'
  year_in_title = bool(re.search(year_pattern, title_upper))
  
  # Full title match: law type + number + year all present
  if law_type_in_title and number_in_title and year_in_title:
    return True
  
  # If the title contains the law type, check if it identifies a DIFFERENT law
  # by having a different number or year - in that case, reject it entirely
  if law_type_in_title:
    # Check if title contains any number after the law type (indicating a numbered law)
    # Pattern: look for numbers that typically appear in law titles (1-4 digits)
    title_has_any_number = bool(re.search(r'\b\d{1,4}\b', title_upper))
    
    if title_has_any_number:
      # Title identifies a numbered law - only accept if it's the RIGHT number and year
      # If number doesn't match OR year doesn't match, this is a different law
      if not number_in_title or not year_in_title:
        return False
  
  # If we get here, the title either:
  # 1. Doesn't contain any recognized law type (e.g., "CODUL MUNCII")
  # 2. Contains the target law type but no number (unlikely but possible)
  # In these cases, allow description matching
  if description and matches_numeric_ids(description, reference_components):
    return True
  
  return False

def search_law_online(reference):
  result = requests.get(
    "https://api.search.brave.com/res/v1/web/search",
    headers={
      "X-Subscription-Token" : brave_api_key,
    },
    params={
      "q": f"{reference} site:legislatie.just.ro",
      "count": 20,
      "country:": "ro",
      "search_lang": "ro",
    },
  ).json()

  # Parse reference components for matching
  reference_components = parse_reference_components(reference)
  
  # Collect matching URLs with their IDs and titles
  matching_urls = []
  for res in result['web']['results']:
    url = res['profile']['url']
    title = res.get('title', '')
    description = res.get('description', '')
    
    # Check if URL is from a trusted domain
    is_trusted = any(trusted_domain in url for trusted_domain in TRUSTED_DOMAINS)
    if not is_trusted:
      continue
    
    # Check if the title or description matches our reference
    if matches_reference(title, description, reference_components):
      url_id = extract_url_id(url)
      matching_urls.append((url, url_id, title))
      
      # Determine if match was in title or description for logging
      title_matches = reference_components and reference_components[0] in title.upper()
      match_location = "title" if title_matches else "description"
      print(f"Matching result ({match_location}): ID={url_id}, Title={title}, URL={url}")
    else:
      print(f"Non-matching result: Title={title}, URL={url}")
  
  # Sort by ID (descending) to get the highest ID first
  matching_urls.sort(key=lambda x: x[1], reverse=True)
  
  if matching_urls:
    best_url, best_id, best_title = matching_urls[0]
    print(f"Selected URL with highest ID: {best_url} (ID={best_id}, Title={best_title})")
    # get_leg_just_ro_content now returns (file_id, normalized_ref)
    file_id, normalized_ref = web_scraper.get_leg_just_ro_content(best_url, reference)
    return file_id, normalized_ref
  
  return None, None
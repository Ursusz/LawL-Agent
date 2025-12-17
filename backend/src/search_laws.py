import os
import asyncio
from PyPDF2 import PdfReader
from .models import bm25, gemini_summary
from .web_scraping import brave_search_api
from .utilities import cloud_file_management
from .progress_tracker import progress_tracker

REFERENCE_DOCS_DIR = '../reference_docs'

def find_cloud_reference(law_ref):
  fileName = f'{law_ref}'
  res = cloud_file_management.search_file_in_cloud(fileName)
  if res is not None:
    return res['id']
  return None

def extract_text_pdf(filepath):
  if filepath is None:
    return 'The text of the law was not found.'
  reader = PdfReader(filepath)
  text = ''
  for page in reader.pages:
    text += page.extract_text() or ''
  return text

def extract_text_txt(filepath):
  if filepath is None:
    return 'The text of the law was not found.'
  text = ''
  with open(filepath, 'r') as f:
    text = f.read() or ''
  return text

def fetch_online_reference(law_ref): #find law on brave api and download it
  # brave_search_api -> ia primul site cel mai relevant (+ de incredere), apoi un web scraper extrage continutul si il salveaza intr-un fisier cu numele {referinta_standardizata}
  print("Web scraping")
  print(f"Searching online for reference {law_ref}")
  fileId, normalized_ref = brave_search_api.search_law_online(law_ref)
  
  # If we got a normalized reference from web scraping, check if it already exists in cloud
  if normalized_ref and fileId is None:
    print(f"Checking if normalized reference {normalized_ref} exists in cloud")
    fileId = find_cloud_reference(f'{normalized_ref}.txt')
    if fileId:
      print(f"Found normalized reference in cloud: {normalized_ref}")
  
  if fileId is None:
    fileId = find_cloud_reference(f'{law_ref}.txt')
  print(f"File ID where local ref is now saved -> {fileId}")
  text = ''
  url = ''
  if fileId is not None:
    # text = extract_text_txt(filepath)
    text, url = fetch_cloud_reference(fileId)
    print("Sucesfully extracted law text from cloud")
  return text, url, normalized_ref

def fetch_cloud_reference(fileId): #downloading from gdrive
  print("Cloud Corpus")
  print("Looking in cloud corpus")
  file_content = cloud_file_management.download_file_content(fileId)
  lines = file_content.splitlines()
  if len(lines) > 1:
    file_content = '\n'.join(lines[1:]) #sterge sursa textului legii (url-ul) de pe primul rand
  url = lines[0]

  return file_content, url 

async def find_laws(references, document_text, session_id: str = None):

  import time
  from .utilities import law_reference_mappings
  
  laws = {}
  
  # Token tracking to stay under 250k tokens/minute
  # Approximate: 1 char ≈ 0.25 tokens (conservative estimate)
  # We'll track input tokens and add delays if needed
  token_budget_per_minute = 200000
  tokens_used_this_minute = 0
  minute_start_time = time.time()
  
  for ref in references:
    print("\n\n")
    print(f"Processing reference {ref}")
    
    # Emit progress: starting to process this reference
    if session_id:
      await progress_tracker.emit_reference_processing_start(session_id, ref)

    law_text = ''
    url = ''
    normalized_ref = None
    
    # Check if we have a mapping for this reference
    print(f"Checking mapping for reference: '{ref}'")
    mapped_ref = law_reference_mappings.get_normalized_reference(ref)
    if mapped_ref:
      print(f"Found mapping: '{ref}' -> '{mapped_ref}'")
      
      # Emit progress: checking cloud for mapped reference
      if session_id:
        await progress_tracker.emit_reference_stage_update(session_id, ref, 'checking_cloud')
      
      # Try to find the file with the normalized name
      fileId = await asyncio.to_thread(find_cloud_reference, f'{mapped_ref}.txt')
      if fileId:
        print(f"Found law using mapping: {ref} -> {mapped_ref}")
        law_text, url = await asyncio.to_thread(fetch_cloud_reference, fileId)
        normalized_ref = mapped_ref
      else:
        # Mapping exists but file not found, continue with normal lookup
        print(f"Mapping exists ({ref} -> {mapped_ref}) but file not found, continuing with normal lookup")
    
    # If not found via mapping, try normal lookup
    if not law_text:
      # Emit progress: checking for law text
      if session_id:
        await progress_tracker.emit_reference_stage_update(session_id, ref, 'checking_cloud')
      
      # First, try to find in cloud with original reference
      fileId = await asyncio.to_thread(find_cloud_reference, f'{ref}.txt')
      
      # If not found and ref looks like a sanitized implicit reference (contains underscores, no numbers),
      # it might have been saved with a normalized name previously
      # Try common normalized patterns
      if fileId is None and '_' in ref and not any(char.isdigit() for char in ref.split('_')[0]):
        # This looks like a sanitized implicit reference (e.g., "Codul_fiscal")
        # Try to find it by searching for common law patterns
        # For now, we'll let the web scraping handle it and save with normalized name
        pass
      
      if fileId is not None:
        law_text, url = await asyncio.to_thread(fetch_cloud_reference, fileId) #download from gdrive
      elif len(law_text) == 0:
        # Emit progress: fetching online
        if session_id:
          await progress_tracker.emit_reference_stage_update(session_id, ref, 'fetching_online')
        
        law_text, url, normalized_ref = await asyncio.to_thread(fetch_online_reference, ref) #browse on brave and scrape the content
        
        # If we got a normalized reference from web scraping, save the mapping
        if normalized_ref and normalized_ref != ref:
          print(f"Saving new mapping: {ref} -> {normalized_ref}")
          law_reference_mappings.add_law_mapping(ref, normalized_ref)
    
    # Use normalized reference as the key if available, otherwise use original ref
    final_ref = normalized_ref if normalized_ref else ref

    if law_text:
      print("Extracting most relevant article")
      print("Extracting most relevant article")
      relevant_articles_with_scores = bm25.get_most_relevant_fragment(law_text=law_text, context=document_text)
      
      # Use the top 1 article for Gemini summary
      top_article = relevant_articles_with_scores[0][0] if relevant_articles_with_scores else ""
      
      # Check for cached summary first
      if session_id:
        await progress_tracker.emit_reference_stage_update(session_id, ref, 'checking_cache')
      
      print(f"Checking for cached summary for {final_ref}")
      cached_summary_file = await asyncio.to_thread(cloud_file_management.search_summary_in_cloud, final_ref)
      
      law_summary_data = None
      if cached_summary_file:
        # Load cached summary
        law_summary_data = await asyncio.to_thread(cloud_file_management.download_summary_content, cached_summary_file['id'])
        if law_summary_data:
          print("[CACHE HIT] Using cached full law summary")
          if session_id:
            await progress_tracker.emit_reference_stage_update(session_id, ref, 'law_summary', cached=True)
      
      # If no cached summary, generate it
      if not law_summary_data:
        print("[CACHE MISS] Generating full law summary")
        
        if session_id:
          await progress_tracker.emit_reference_stage_update(session_id, ref, 'generating_law_summary', cached=False)
        
        # Estimate tokens for full law summary call
        estimated_input_chars = len(law_text) + 500  # law_text + prompt overhead
        estimated_input_tokens = int(estimated_input_chars * 0.35)
        
        # Check if we need to wait to stay under rate limit
        current_time = time.time()
        elapsed_time = current_time - minute_start_time
        
        if elapsed_time >= 60:
          # Reset counter for new minute
          tokens_used_this_minute = 0
          minute_start_time = current_time
          elapsed_time = 0
        
        # If adding this call would exceed budget, wait
        if tokens_used_this_minute + estimated_input_tokens > token_budget_per_minute:
          wait_time = 60 - elapsed_time + 1  # Wait until next minute + 1 sec buffer
          print(f"[RATE LIMIT] Approaching token limit ({tokens_used_this_minute}/{token_budget_per_minute}), waiting {wait_time:.1f}s")
          await asyncio.sleep(wait_time)
          tokens_used_this_minute = 0
          minute_start_time = time.time()
        
        # Generate full law summary
        print("Generating full law summary with Gemini")
        law_summary_data = await asyncio.to_thread(gemini_summary.get_full_law_summary, law_text)
        
        # Update token counter
        tokens_used_this_minute += estimated_input_tokens
        print(f"[RATE LIMIT] Tokens used this minute: {tokens_used_this_minute}/{token_budget_per_minute}")
        
        # Save to cache if successful
        if law_summary_data:
          print("Saving full law summary to cache")
          await asyncio.to_thread(cloud_file_management.save_summary_in_cloud, final_ref, law_summary_data)
      
      # Always generate targeted article summary (not cached, depends on context)
      print("Generating targeted article summary")
      
      if session_id:
        await progress_tracker.emit_reference_stage_update(session_id, ref, 'generating_article_summary', cached=False)
      
      # Estimate tokens for targeted article summary call
      estimated_input_chars = len(law_text) + len(top_article) + 500
      estimated_input_tokens = int(estimated_input_chars * 0.35)
      
      # Check if we need to wait to stay under rate limit
      current_time = time.time()
      elapsed_time = current_time - minute_start_time
      
      if elapsed_time >= 60:
        # Reset counter for new minute
        tokens_used_this_minute = 0
        minute_start_time = current_time
        elapsed_time = 0
      
      # If adding this call would exceed budget, wait
      if tokens_used_this_minute + estimated_input_tokens > token_budget_per_minute:
        wait_time = 60 - elapsed_time + 1
        print(f"[RATE LIMIT] Approaching token limit ({tokens_used_this_minute}/{token_budget_per_minute}), waiting {wait_time:.1f}s")
        await asyncio.sleep(wait_time)
        tokens_used_this_minute = 0
        minute_start_time = time.time()
      
      # Generate targeted article summary
      article_summary_data = await asyncio.to_thread(gemini_summary.get_targeted_article_summary, '\n'.join([article for article, _ in relevant_articles_with_scores]), document_text)
      
      # Update token counter
      tokens_used_this_minute += estimated_input_tokens
      print(f"[RATE LIMIT] Tokens used this minute: {tokens_used_this_minute}/{token_budget_per_minute}")
      
      # Combine results
      if law_summary_data and article_summary_data:
        print("Successfully generated/retrieved all summaries")
        
        # Emit progress: reference complete
        if session_id:
          await progress_tracker.emit_reference_complete(session_id, ref, success=True)
        
        # Use original ref as key for frontend compatibility
        # But include normalized_ref for future lookups
        laws[ref] = {
          "url": url if len(url) > 0 else "No url available",
          "law": law_text,
          "law_summary": law_summary_data.get('law_summary', ''),
          "law_simplified": law_summary_data.get('law_simplified', ''),
          "relevant_article": top_article,
          "relevant_articles": [{"text": text, "score": score} for text, score in relevant_articles_with_scores],
          "articles_summary": article_summary_data.get('articles_summary', ''),
        }
        # Add normalized reference if available (for future lookups)
        if normalized_ref and normalized_ref != ref:
          laws[ref]["normalized_reference"] = normalized_ref
      elif law_summary_data and not article_summary_data:
        # Partial success - have full summary but article summary failed
        if session_id:
          await progress_tracker.emit_reference_complete(session_id, ref, success=True)
        
        laws[ref] = {
          "url": url if len(url) > 0 else "No url available",
          "law": law_text,
          "law_summary": law_summary_data.get('law_summary', ''),
          "law_simplified": law_summary_data.get('law_simplified', ''),
          "relevant_article": top_article,
          "relevant_articles": [{"text": text, "score": score} for text, score in relevant_articles_with_scores],
          "articles_summary": "Failed to generate article summary",
        }
        if normalized_ref and normalized_ref != ref:
          laws[ref]["normalized_reference"] = normalized_ref
      else:
        # Complete failure
        if session_id:
          await progress_tracker.emit_reference_complete(session_id, ref, success=False, error="Gemini failed to generate summaries")
        
        laws[ref] = {
          "ERROR": f"Gemini failed to generate summaries."
        }
    else:
      if session_id:
        await progress_tracker.emit_reference_complete(session_id, ref, success=False, error="Law text not found")
      
      laws[ref] = {
        "ERROR": f"Law text not found."
      }
  return laws


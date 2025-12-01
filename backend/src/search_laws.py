import os
from PyPDF2 import PdfReader
from .models import bm25, gemini_summary
from .web_scraping import brave_search_api
from .utilities import cloud_file_management

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
  fileId = brave_search_api.search_law_online(law_ref)
  if fileId is None:
    fileId = find_cloud_reference(f'{law_ref}.txt')
  print(f"File ID where local ref is now saved -> {fileId}")
  text = ''
  url = ''
  if fileId is not None:
    # text = extract_text_txt(filepath)
    text, url = fetch_cloud_reference(fileId)
    print("Sucesfully extracted law text from cloud")
  return text, url

def fetch_cloud_reference(fileId): #downloading from gdrive
  print("Cloud Corpus")
  print("Looking in cloud corpus")
  file_content = cloud_file_management.download_file_content(fileId)
  lines = file_content.splitlines()
  if len(lines) > 1:
    file_content = '\n'.join(lines[1:]) #sterge sursa textului legii (url-ul) de pe primul rand
  url = lines[0]

  return file_content, url 

def find_laws(references, document_text):
  laws = {}
  for ref in references:
    print("\n\n")
    print(f"Processing reference {ref}")

    law_text = ''
    url = ''
    fileId = find_cloud_reference(f'{ref}.txt')
    if fileId is not None:
      law_text, url = fetch_cloud_reference(fileId) #download from gdrive
    elif len(law_text) == 0:
      law_text, url = fetch_online_reference(ref) #browse on brave and scrape the content

    if law_text:
      print("Extracting most relevant article")
      relevant_article = bm25.get_most_relevant_fragment(law_text=law_text, context=document_text)
      print("Waiting for gemini information")
      gemini_information = gemini_summary.get_gemini_informations_about_law(law_text, relevant_article)
      if gemini_information:
        print(f"Current gemini info size -> {len(gemini_information)}")
      else:
        print("Gemini returned None")
      # gemini_information[0] -> sumar lege intreaga
      # gemini_information[1] -> lege intreaga simplificata
      # gemini_information[2] -> sumar articol relevant
      # TODO: implementare caz none standardizare
      if ref is None:
        laws[ref] = {
          "ERROR": f"Error for {ref} -> Could not normalize law title."
        }
      if gemini_information is not None:
        if len(gemini_information) < 3 or gemini_information is None:
          laws[ref] = {
            "ERROR": f"Gemini failed to return structured format."
          }
        else:
          laws[ref] = {
            "url": url if len(url) > 0 else "No url available",
            "law": law_text,
            "law_summary": gemini_information[0],
            "law_simplified": gemini_information[1],
            "relevant_article": relevant_article,
            "articles_summary": gemini_information[2],
          }
      else:
        laws[ref] = {
          "ERROR": f"Gemini did not return any answer."
        }
  return laws

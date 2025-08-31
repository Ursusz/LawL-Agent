import os
from PyPDF2 import PdfReader
from models import bm25, gemini_summary
from web_scraping import brave_search_api
from utilities import standardize_law_title, cloud_file_management

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

def fetch_online_reference(law_ref):
  # brave_search_api -> ia primul site cel mai relevant (+ de incredere), apoi un web scraper extrage continutul si il salveaza intr-un fisier cu numele {referinta_standardizata}
  print("Web scraping")
  print(f"Searching online for reference {law_ref}")
  brave_search_api.search_law_online(law_ref)
  fileId = find_cloud_reference(f'{law_ref}.txt')
  print(f"File ID where local ref is now saved -> {fileId}")
  text = ''
  if fileId is not None:
    # text = extract_text_txt(filepath)
    text = fetch_cloud_reference(fileId)
    print("Sucesfully extracted law text from cloud")
  return text

def fetch_cloud_reference(fileId):
  print("Cloud Corpus")
  print("Looking in cloud corpus")
  file_content = cloud_file_management.download_file_content(fileId)
  return file_content

def find_laws(references, document_text):
  laws = {}
  for ref in references:
    print("\n\n")
    print(f"Processing reference {ref}")
    result = standardize_law_title.standardize_law_title(ref)
    print(f"Normalized law ref -> {result}")

    law_reference_standard = ''
    tip_act = None
    ###################################################### AICI STANDARDIZEZ TITLUL LEGII #####################################################33
    if result is not None:
      if len(result) == 3:
        tip_act, nr_act, an_act = result
        law_reference_standard = f'{tip_act}_{nr_act}_{an_act}'
      elif len(result) == 4:
        tip_act, nr_act1, nr_act2, an_act = result
        law_reference_standard = f'{tip_act}_{nr_act1}_{nr_act2}_{an_act}'

      law_text = ''
      if tip_act is not None:
        fileId = find_cloud_reference(f'{law_reference_standard}.txt')
        if fileId is not None:
          law_text = fetch_cloud_reference(fileId)
        elif len(law_text) == 0:
          law_text = fetch_online_reference(law_reference_standard)


    if law_text:
      print("Extracting most relevant article")
      relevant_article = bm25.get_most_relevant_fragment(law_text=law_text, context=document_text)
      print("Waiting for gemini information")
      gemini_information = gemini_summary.get_gemini_informations_about_law(law_text, relevant_article)
      # gemini_information[0] -> sumar lege intreaga
      # gemini_information[1] -> lege intreaga simplificata
      # gemini_information[2] -> sumar articol relevant
      # TODO: implementare caz none standardizare
      if result is None:
        laws[ref] = {
          "ERROR": f"Error for {ref} -> Could not normalize law title."
        }
      else:
        laws[ref] = {
          "law": law_text,
          "law_summary": gemini_information[0],
          "law_simplified": gemini_information[1],
          "relevant_article": relevant_article,
          "relevant_article_summary": gemini_information[2],
        }
  return laws
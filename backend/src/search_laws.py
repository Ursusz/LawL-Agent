import os
from PyPDF2 import PdfReader
from models import bm25, gemini_summary
from web_scraping import brave_search_api
from utilities import parse_law_title, standardize_law_title

REFERENCE_DOCS_DIR = '../reference_docs'

def find_local_reference(law_ref):
  # mapping = {
  #     'Ordinului 1855/2022': 'OMF_1855_2022.pdf',
  # }
  # fname = mapping.get(law_ref)
  # if fname:
  #     fpath = os.path.join(REFERENCE_DOCS_DIR, fname)
  #     if os.path.exists(fpath):
  #         return fpath
  # return None
  if os.path.isdir(REFERENCE_DOCS_DIR):
    for file in os.listdir(REFERENCE_DOCS_DIR):
      if file == f'{law_ref}.txt':
        fpath = os.path.join(REFERENCE_DOCS_DIR, file)
        if os.path.isfile(fpath):
          return fpath
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
  brave_search_api.search_law_online(law_ref)
  filepath = find_local_reference(law_ref)
  text = extract_text_txt(filepath)
  return text

def fetch_local_reference(law_ref):
  print("Local Corpus")
  filepath = find_local_reference(law_ref)
  text = extract_text_txt(filepath)
  return text

def find_laws(references, document_text):
  laws = {}
  for ref in references:
    result = standardize_law_title.standardize_law_title(ref)
    law_reference_standard = ''
    tip_act, nr_act, an_act = result
    law_reference_standard = f'{tip_act}_{nr_act}_{an_act}'
    # tip_act, nr_act, an_act = standardize_law_title.standardize_law_title(ref)
    # law_reference_standard = f'{tip_act}_{nr_act}_{an_act}'
    law_text = ''
    # momentan, tip_act poate fi None din cauza patternului regex, poate referinta nu respecta patternul
    if tip_act is not None:
      if os.path.isdir(REFERENCE_DOCS_DIR):
        # iterez prin fisierele din reference_docs, daca gasesc un fisier cu acelasi nume ca referinta, fetch-uiesc local
        for file in os.listdir(REFERENCE_DOCS_DIR):
          print(f"{law_reference_standard}.txt", f"  {file}")
          if file == f'{law_reference_standard}.txt':
            fpath = os.path.join(REFERENCE_DOCS_DIR, file)
            if os.path.isfile(fpath):
              law_text = fetch_local_reference(law_reference_standard)
              break
        # altfel aplic logica de web scraping
        if len(law_text) == 0:
          law_text = fetch_online_reference(law_reference_standard)
    if law_text:
      relevant_article = bm25.get_most_relevant_fragment(law_text=law_text, context=document_text)
      gemini_information = gemini_summary.get_gemini_informations_about_law(law_text, relevant_article)
      # gemini_information[0] -> sumar lege intreaga
      # gemini_information[1] -> lege intreaga simplificata
      # gemini_information[2] -> sumar articol relevant
      laws[ref] = {
        "law": law_text,
        "law_summary": gemini_information[0],
        "law_simplified": gemini_information[1],
        "relevant_article": relevant_article,
        "relevant_article_summary": gemini_information[2],
      }
  return laws
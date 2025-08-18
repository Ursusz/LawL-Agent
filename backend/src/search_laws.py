import os
from PyPDF2 import PdfReader
from models import bm25, gemini_summary

REFERENCE_DOCS_DIR = '../reference_docs'
TRUSTED_DOMAINS = [
    'legislatie.just.ro',
    'www.just.ro',
    'mfinante.gov.ro'
]

def find_local_reference(law_ref):
    mapping = {
        'Ordinului 1855/2022': 'OMF_1855_2022.pdf',
    }
    fname = mapping.get(law_ref)
    if fname:
        fpath = os.path.join(REFERENCE_DOCS_DIR, fname)
        if os.path.exists(fpath):
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

def fetch_law_online(law_ref):
    # Dummy implementation: in production, use search APIs or custom scraping per domain
    # Only fetch from trusted domains
    print(f"[INFO] Would search online for '{law_ref}' in trusted domains: {TRUSTED_DOMAINS}")
    # Example: return requests.get(url).text
    return None

def fetch_local_reference(law_ref):
    filepath = find_local_reference(law_ref)
    text = extract_text_pdf(filepath)
    return text

def find_laws(references, document_text):
    laws = {}
    for ref in references:
        law_text = fetch_local_reference(ref)
        if law_text:
            relevant_article = bm25.get_most_relevant_fragment(law_text=law_text, context=document_text)
            relevant_article_summary = gemini_summary.get_text_summary(relevant_article)
            law_summary = gemini_summary.get_text_summary(law_text)
            law_simplified = gemini_summary.get_law_text_simplified(law_text)
            laws[ref] = {
                "law": law_text,
                "law_summary": law_summary,
                "law_simplified": law_simplified,
                "relevant_article": relevant_article,
                "relevant_article_summary": relevant_article_summary,
            }
    return laws
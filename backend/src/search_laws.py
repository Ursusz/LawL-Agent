import os
from PyPDF2 import PdfReader

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

def find_laws(references):
    details = {}
    for ref in references:
        text = fetch_local_reference(ref)
        if text:
            details[ref] = text
    
    return details
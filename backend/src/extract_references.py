import re
from bs4 import BeautifulSoup
from sklearn.metrics.pairwise import cosine_similarity

LAW_REGEXES = [
    r"Legea nr\.\s*\d+/\d{4}",
    r"Ordinul(?:ui)?\s*\d+/\d{4}",
    r"HG\s*\d+/\d{4}"
]
    
def extract_law_references(text):
    refs = set()
    for regex in LAW_REGEXES:
        matches = re.findall(regex, text)
        refs.update(matches)
    return list(refs)
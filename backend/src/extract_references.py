import re

LAW_REGEXES = [
    r"Legii nr\.\s*\d+/\d{4}",
    r"Ordinul(?:ui)?\s*\d+/\d{4}",
    r"HG\s*\d+/\d{4}"
]
    
def extract_law_references(text):
    refs = set()
    for regex in LAW_REGEXES:
        matches = re.findall(regex, text)
        refs.update(matches)
    return list(refs)
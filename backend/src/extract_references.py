import re

LAW_REGEXES = [
    r"(?:Legea|Legii|L\.?)\s*(?:nr\.?)\s*\d+(?:/\d{4})?",
    r"(?:Hotărârea|Hotararea\s+Guvernului|H\.?G\.?)\s*(?:nr\.?)\s*\d+(?:/\d{4})?",
    r"(?:Ordonanța|Ordonanței|Ordonanta|Ordonantei|O\.?G\.?)\s*(?:nr\.?)\s*\d+(?:/\d{4})?",
    r"(?:Ordonanța|Ordonanta\s+de\s+urgență|urgenta|O\.?U\.?G\.?)\s*(?:nr\.?)\s*\d+(?:/\d{4})?",
    r"(?:Codul|Cod)(?:\s+(?:Civil|Penal|Muncii|Fiscal))?",
    r"(?:Decizia|Hotărârea|Hotararea|Ordinul|Decretul|Instrucțiunea|Instructiunea|Norma)\s*(?:nr\.?)\s*\d+(?:/\d{4})?"
]
    
def extract_law_references(text):
    refs = set()
    for regex in LAW_REGEXES:
        matches = re.findall(regex, text)
        refs.update(matches)
    return list(refs)
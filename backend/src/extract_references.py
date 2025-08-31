import re

LAW_REGEXES = [
    r"(?:Lege|Legea|Legii|L\.?)\s*(?:[^\d]*)?\s*(?:nr\.?\s*)?\d+(?:/\d+)*",
    r"(?:Hotărârea|Hotararea\s+Guvernului|H\.?G\.?)\s*(?:nr\.?)\s*\d+(?:/\d+)*",
    r"(?:Ordonanța|Ordonanței|Ordonanta|Ordonantei|O\.?G\.?)\s*(?:nr\.?)\s*\d+(?:/\d+)*",
    r"(?:Ordonanța|Ordonanta\s+de\s+urgență|Ordonanta\s+de\s+urgenta|O\.?U\.?G\.?)\s*(?:nr\.?)\s*\d+(?:/\d+)*",
    r"(?:Codul|Cod)(?:\s+(?:Civil|Penal|Muncii|Fiscal))?",
    r"(?:Decizia|Hotărârea|Hotararea|Ordinul|Decretul|Instrucțiunea|Instructiunea|Norma|Norma\s+metodologica)\s*(?:nr\.?)\s*\d+(?:/\d+)*"
]
    
def extract_law_references(text):
    refs = set()
    for regex in LAW_REGEXES:
        matches = re.findall(regex, text)
        refs.update(matches)
    return list(refs)
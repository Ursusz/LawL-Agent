import re
from .utilities import standardize_law_title

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
        std_refs = [standardize_law_title.standardize_law_title(ref) for ref in matches]
        
        if std_refs:
            for std_ref in std_refs:
                law_reference_standard = ''
                if std_ref is not None:
                    if len(std_ref) == 3:
                      tip_act, nr_act, an_act = std_ref
                      law_reference_standard = f'{tip_act}_{nr_act}_{an_act}'
                    elif len(std_ref) == 4:
                      tip_act, nr_act1, nr_act2, an_act = std_ref
                      law_reference_standard = f'{tip_act}_{nr_act1}_{nr_act2}_{an_act}'
                    else:
                        continue
                if law_reference_standard != '':
                    refs.add(law_reference_standard)
    return list(refs)
import re
import logging

logging.getLogger("stanza").setLevel(logging.WARNING)

def standardize_law_title(law_text):
    clean_text = law_text.lower()
    
    clean_text = re.sub(r'\(.*?\)', '', clean_text)
    
    clean_text = re.sub(r'[\/\.]', ' ', clean_text)
    
    clean_text = re.sub(r'hotărârea|hotararea guvernului|h g\.?', 'hg', clean_text)
    clean_text = re.sub(r'ordonanța|ordonanta de urgență|urgenta|o\.?u\.?g\.?', 'oug', clean_text)
    clean_text = re.sub(r'legea|legii|lege', 'lege', clean_text)
    clean_text = re.sub(r'decizia|decretul|hotărâre|hotarare|ordinul', 'act_normativ', clean_text)
    
    clean_text = re.sub(r'\b(nr|din|ianuarie|februarie|martie|aprilie|mai|iunie|iulie|august|septembrie|octombrie|noiembrie|decembrie)\b', '', clean_text)

    processed_parts = clean_text.split()
    
    lemmatized_law = '_'.join(processed_parts).upper()

    match = re.search(r'([A-ZĂÎÂŞȚ_]+)_?(\d+).*?_?(\d{4})', lemmatized_law)

    if match:
        law_type = match.group(1).replace('Ă', 'A').replace('Î', 'I').replace('Â', 'A').replace('Ș', 'S').replace('Ț', 'T')
        law_number = match.group(2)
        law_year = match.group(3)
        
        return law_type, law_number, law_year

    return None, None, None
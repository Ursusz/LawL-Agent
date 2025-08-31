import re
import unicodedata
import stanza

nlp = stanza.Pipeline("ro", processors="tokenize,pos,lemma")

def lemmatize(text):
  text = text.lower()
  doc = nlp(text)
  lemmatized_text = ''
  for sent in doc.sentences:
    for word in sent.words:
    #   print(word, word.lemma)
      lemmatized_text += word.lemma + ' '
  return lemmatized_text.upper()

def normalize_text(text: str) -> str:
    # eliminare diacritice
    text = ''.join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn')
    return text.lower()

def extract_law_prefix(text: str) -> str:
    act_pattern = re.compile(
        r'\b('
        r'lege|'
        r'hotarare\s+de\s+guvern|hotarare\s+guvern|hotarare|'
        r'ordonanta\s+de\s+urgenta|ordonanta|'
        r'oug?|'
        r'ordin|'
        r'decizie'
        r')\b',
        flags=re.IGNORECASE
    )

    match = act_pattern.search(text)
    if match:
       prefix = match.group(1).upper()
       return prefix.replace(' ', '_')
    return None
   

def standardize_law_title(law_title: str) -> str:
    if not isinstance(law_title, str):
        return None

    text = lemmatize(law_title)
    text = normalize_text(text)
    
    prefix_pattern = r'\b(lege|hotarare|decizie|ordin|ordonanta|ou(g)?)\b'
    prefix_match = re.search(prefix_pattern, text)
    if not prefix_match:
        return None

    prefix = extract_law_prefix(text)

    year_match = re.search(r'(?:19\d{2}|20\d{2})(?!.*(?:19\d{2}|20\d{2}))', text)
    if not year_match:
        return None
    year = year_match.group(0)

    ## SCOT ANUL DIN TITLUL DE LEGE
    text = re.sub(r'(?:19\d{2}|20\d{2})(?!.*(?:19\d{2}|20\d{2}))', '', text)

    numbers_pattern = r'\b\d+(?:/\d+)?\b'

    numbers_match = re.search(numbers_pattern, text)
    numbers = numbers_match.group(0).split('/')

    # standardized_name = ''
    if numbers is not None:
        if len(numbers) == 2:
        #    standardized_name = f'{prefix}_{numbers[0]}_{numbers[1]}_{year}'
            return prefix, numbers[0], numbers[1], year
        elif len(numbers) == 1:
        #    standardized_name = f"{prefix}_{numbers[0]}_{year}"
            return prefix, numbers[0], year
    return None


# law_titles = [
#     "Legea nr. 53/2003",
#     "Legea 287 din 2009",
#     "HOTĂRÂRE DE GUVERN NR. 856 DIN 2020",
#     "Ordonanta de urgenta nr. 195/2002",
#     "Legea nr. 360/2023",
#     "Hotărârea Guvernului nr. 100/2023",
#     "OUG nr. 99 din 2006",
#     "Ordin nr. 1855/2022",
#     "Ordonanta nr. 30 din 2017",
#     "LEGE nr. 31 din 16 noiembrie 1990 (*republicată*)",
#     "Ordonanța de urgență nr. 119 din 24 octombrie 2022",
#     "Hotărârea nr. 1000 din 27 decembrie 2023",
#     "Ordinul nr. 1761/2006 al ministrului sănătății",
#     "Decizia nr. 99/100/2020",
#     "Ordinul nr. 483/184 din 10 iunie 1999",
#     "Legea 188 din 1999",
#     "OUG 117 din 2022"
# ]

# for law_title in law_titles:
    # print(law_title, "-->", standardize_law_title(law_title))
    # standardize_law_title(law_title)

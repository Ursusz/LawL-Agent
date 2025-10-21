from rank_bm25 import BM25Okapi
import re

ART_FRAGMENT_REGEX = r'(?:Articolul|ART\.)\s+(?:[IVXLCDM]+|\d+)[\s\S]*?(?=(?:Articolul|ART\.)\s+(?:[IVXLCDM]+|\d+)|$)'

def is_example_article(article_text):
    example_regex = r'Exemplul|Exemple privind'
    return bool(re.search(example_regex, article_text, re.IGNORECASE))

def extract_law_fragments(law_text):
    fragments = re.findall(ART_FRAGMENT_REGEX, law_text)
    
    filtered_articles = []
    for fragm in fragments:
        if not is_example_article(fragm):
            filtered_articles.append(fragm)

    return filtered_articles

def tokenize(fragment):
    return re.findall(r'\w+', fragment.lower())

def get_most_relevant_fragment(law_text, context):
    text_fragments = extract_law_fragments(law_text)

    if not text_fragments:
        return "Eroare: Nu s-au putut extrage fragmente/articole din textul legii." 

    tokenized_fragments = [tokenize(fragment) for fragment in text_fragments]

    bm25 = BM25Okapi(tokenized_fragments)

    query_tokens = tokenize(context)

    scores = bm25.get_scores(query_tokens)

    most_relevant_fragment_index = sorted(range(len(scores)), key=lambda x: scores[x], reverse=True)[:1]

    return text_fragments[most_relevant_fragment_index[0]]

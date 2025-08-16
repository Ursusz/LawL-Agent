from rank_bm25 import BM25Okapi
import re

ART_FRAGMENT_REGEX = r'ART\. \d+[\s\S]*?(?=ART\. \d+|$)'


def extract_law_fragments(law_text):
    fragments = re.findall(ART_FRAGMENT_REGEX, law_text)
    return fragments

def tokenize(fragment):
    return re.findall(r'\w+', fragment.lower())

def get_most_relevant_fragment(law_text, context):
    text_fragments = extract_law_fragments(law_text)
    tokenized_fragments = [tokenize(fragment) for fragment in text_fragments]

    bm25 = BM25Okapi(tokenized_fragments)

    query_tokens = tokenize(context)

    scores = bm25.get_scores(query_tokens)

    most_relevant_fragment_index = sorted(range(len(scores)), key=lambda x: scores[x], reverse=True)[:1]

    return text_fragments[most_relevant_fragment_index[0]]

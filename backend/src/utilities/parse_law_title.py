import re
import stanza

# stanza.download("ro")

nlp = stanza.Pipeline("ro", processors="tokenize,pos,lemma")

def lemmatize(text):
  doc = nlp(text)
  lemmatized_law = ''
  for sent in doc.sentences:
    for word in sent.words:
      if word.text != 'nr.':
        lemmatized_law += word.lemma + '_'
      else:
        lemmatized_law += 'nr._'
  return lemmatized_law.upper()

def parse_law_title(law_title):
  lemmatized_law = lemmatize(law_title)
  match = re.search(r'([A-Z]+)_NR\._(\d+)/(\d{4})', lemmatized_law)
  if match:
    tip_act = match.group(1)
    nr_act = match.group(2)
    an_act = match.group(3)

    return tip_act, nr_act, an_act
  
  return None, None, None

print(parse_law_title('legii nr. 360/2023'))
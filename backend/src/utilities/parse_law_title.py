import os
import re
import stanza
import logging

logging.getLogger("stanza").setLevel(logging.WARNING)

home_dir = os.path.expanduser("~")
stanza_dir_path = os.path.join(home_dir, "stanza_resources", "ro")

if not os.path.isdir(stanza_dir_path):
    stanza.download("ro")


#### OLD VERSION!!

nlp = stanza.Pipeline("ro", processors="tokenize,pos,lemma")

def lemmatize(text):
  text = text.lower()
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
  #LEGE_NR._360/2023_
  match = re.search(r'([A-Z]+)_NR\._(\d+)/(\d{4})', lemmatized_law)
  if match:
    return match.group(1), match.group(2), match.group(3)

  #LEGE_NR._360_DIN_2023_
  match = re.search(r'([A-Z]+)_NR\._(\d+)_DIN_.*?(\d{4})', lemmatized_law)
  if match:
      return match.group(1), match.group(2), match.group(3)
  
  return None, None, None

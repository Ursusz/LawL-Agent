import requests
from lxml import html
import re, os
from utilities import parse_law_title

def get_leg_just_ro_content(url):
  response = requests.get(url)
  tree = html.fromstring(response.content)

  xpath_article_titles = "//*[starts-with(@id, 'id_art') and substring(@id, string-length(@id) - 2, 3) = 'ttl' and not(ancestor::*[contains(@class, 'S_ANX_BDY')])]"
  article_titles = tree.xpath(xpath_article_titles)

  xpath_article_contents = "//span[@class='S_ART_BDY']"
  article_contents = tree.xpath(xpath_article_contents)

  xpath_law_title = "//span[@class='S_DEN']"
  law_title = tree.xpath(xpath_law_title)

  law = ""
  for index in range(len(article_titles)):
    law += article_titles[index].text_content() + "\n" + article_contents[index].text_content().replace("...", "") + "\n"

  tip_act, nr_act, an_act = parse_law_title.parse_law_title(law_title[0].text_content())
  
  if tip_act is not None:
    file_name = f"{tip_act}_{nr_act}_{an_act}.txt"
    folder = "../reference_docs"
    if not os.path.exists(folder):
      os.makedirs(folder)

    file_saving_location = os.path.join(folder, file_name)
    with open(file_saving_location, "w") as file:
      file.write(law)
    file.close()    
import requests
from lxml import html

def extract_content(hrefs):
  for href in hrefs:
      try:
        response = requests.get(href)
        response.raise_for_status()
      except requests.exceptions.RequestException as e:
        print(f"Error accessing web page: {e}")

      tree = html.fromstring(response.content)
      xpath_main = '//*[starts-with(@id, "post-")]'
      main_content = tree.xpath(xpath_main)

      full_text = ''
      if main_content:
        main_element = main_content[0]

        excluded_related_content = main_element.xpath('.//*[@id="related-articles-container"]')
        excluded_entry_meta = main_element.xpath('/html/body/div[1]/div[2]/div/div/main/article/div/header/div')
        if excluded_related_content:
          excluded_related_content[0].getparent().remove(excluded_related_content[0])
        if excluded_entry_meta:
          excluded_entry_meta[0].getparent().remove(excluded_entry_meta[0])

        full_text = main_element.text_content().strip()

  return full_text
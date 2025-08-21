import requests
from lxml import html
import os
from sample_files_extract import chrome_driver
FOLDER_PATH = './sample_files/educatie'

if not os.path.exists:
  os.makedirs(FOLDER_PATH)

##### EXTRAGERE {categorii_educatie}
main_page_url = 'https://modelacte.ro/categorie/educatie/'
response = requests.get(main_page_url)
tree = html.fromstring(response.content)
xpath_urls = '//a'
page_urls = tree.xpath(xpath_urls)
urls = []
for page_url in page_urls:
  url = page_url.get('href')
  if 'educatie' in url and 'page' not in url and len(url) > 44:
    urls.append(url)
urls = set(urls)
#####

## 1. MAIN_PAGE -> categorie/educatie/{categorii_educatie}
## 2. Iterez prin link-urile catre fiecare fisier din {categorii_educatie} -> salvez link-urile -> iterez prin ele si salvez textul

driver = chrome_driver.ChromeDriver(urls)
html_contents = driver.extract_html_contents()

for url in urls:
  ##### EXTRAGERE LINK-URI CATRE FIECARE FISIER DIN {categorii_educatie}
  tree = html.fromstring(html_contents[url][0])
  xpath_articles = '//article'
  articles = tree.xpath(xpath_articles)
  hrefs = [art.xpath('.//a')[0].get('href') for art in articles]
  #####

  for index, href in enumerate(hrefs):
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

    file_name = f'sample_file_{index}.txt'
    file_path = os.path.join(FOLDER_PATH, file_name)

    with open(file_path, 'w') as file:
      file.write(full_text)

    file.close()
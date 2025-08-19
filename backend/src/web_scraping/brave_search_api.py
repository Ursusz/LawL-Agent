import requests
from dotenv import load_dotenv
import os
from web_scraping import web_scraper
import json

load_dotenv()
brave_api_key = os.getenv("BRAVE_SEARCH_API_KEY")

TRUSTED_DOMAINS = [
    'legislatie.just.ro'
    # 'lege5.ro'
]

def search_law_online(reference):
  result = requests.get(
    "https://api.search.brave.com/res/v1/web/search",
    headers={
      "X-Subscription-Token" : brave_api_key,
    },
    params={
      "q": f"{reference}",
      "count": 20,
      "country:": "ro",
      "search_lang": "ro",
    },
  ).json()

  folder_path = 'web_scraping/web_search_res'
  if not os.path.exists(folder_path):
    os.makedirs(folder_path)
  file_name = "help.json"
  file_path = os.path.join(folder_path, file_name)
  with open(file_path, 'w') as file:
    file.write(json.dumps(result).replace("'", '"').replace("False", "false").replace("True", "true"))
  file.close()

  urls = []
  for res in result['web']['results']:
    url = res['profile']['url']
    for trusted_domain in TRUSTED_DOMAINS:
      if trusted_domain in url:
        urls.append(url)
  web_scraper.get_leg_just_ro_content(urls[0])
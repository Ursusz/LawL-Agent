import requests
from dotenv import load_dotenv
import os
from . import web_scraper
import json

load_dotenv()
brave_api_key = os.getenv("BRAVE_SEARCH_API_KEY")

TRUSTED_DOMAINS = [
    'legislatie.just.ro'
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

  urls = []
  for res in result['web']['results']:
    url = res['profile']['url']
    for trusted_domain in TRUSTED_DOMAINS:
      if trusted_domain in url:
        urls.append(url)

  if 'legislatie.just.ro' in urls[0]:
    print(urls[0])
    return web_scraper.get_leg_just_ro_content(urls[0], reference)
  return None
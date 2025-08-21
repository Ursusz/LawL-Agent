from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

class ChromeDriver():
  def __init__(self, urls):
    self.service = Service(ChromeDriverManager().install())
    self.driver = webdriver.Chrome(service=self.service)
    self.url_list = urls
    self.html_contents = {}

    for url in self.url_list:
      self.html_contents[url] = []

  def extract_html_content_from_page(self, url):
    print(F"EXTRACTING CONTENT --- {url}")
    self.driver.get(url)
    scroll_limit = 20
    scroll_count = 0

    while(scroll_count < scroll_limit):
      self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
      time.sleep(3)
      scroll_count += 1

    full_html_content = self.driver.page_source
    self.html_contents[url].append(full_html_content)
  
  def extract_html_contents(self):
    for url in self.url_list:
      self.extract_html_content_from_page(url)

    self.driver.quit()
    return self.html_contents
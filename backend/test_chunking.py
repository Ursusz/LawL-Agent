"""Test the data-list-text chunking logic."""
import requests
from lxml import html
import re

url = 'https://legislatie.just.ro/Public/DetaliiDocumentAfis/260205'
response = requests.get(url)
tree = html.fromstring(response.content)

# Extract using data-list-text chunking
list_items = tree.xpath('//*[@data-list-text]')
content_text = ""
processed_parents = set()

for item in list_items:
    list_text = item.get('data-list-text', '')
    
    # Skip deeply nested items
    if list_text.count('.') > 1:
        continue
    
    children = tree.xpath(f'//*[@data-list-text and starts-with(@data-list-text, "{list_text}.")]')
    
    # Get item content - look for direct <p> tag
    direct_p = item.xpath('./p')
    if direct_p:
        item_content = direct_p[0].text_content().strip()
    else:
        item_content = item.text_content().strip().split('\n')[0].strip()
    
    if children:
        processed_parents.add(list_text)
        content_text += f"{list_text} {item_content}\n"
        
        for child in children:
            child_list_text = child.get('data-list-text', '')
            if child_list_text.count('.') == 1:
                child_p = child.xpath('./p')
                if child_p:
                    child_content = child_p[0].text_content().strip()
                else:
                    child_content = child.text_content().strip().split('\n')[0].strip()
                content_text += f"  {child_list_text} {child_content}\n"
    else:
        if list_text not in processed_parents:
            content_text += f"{list_text} {item_content}\n"

print('Structured content preview (first 1500 chars):')
print(content_text[:1500])
print(f'\n...Total: {len(content_text)} chars')

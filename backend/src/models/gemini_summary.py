from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
import json
import datetime
import re

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# Extrage referințele legislative din documentul atașat, găsește legile respective în surse primare pe internet (de exemplu pe site-ul legislatie.just.ro) și extrage fragmentele de lege relevante pentru document, sumarizând elementele cheie. Justifică informațiile extrase prin referințe la surse primare. 
# 2. Write a simplified version of the law text, making it easy to understand for someone unfamiliar with the topic.
#  "simplified_law_text": "",

TASK_PROMPT = """
** TASKS:

1. Write a summary for the given law text, covering the most important 5 key aspects.
2. Write a summary for the given articles extracted from the same law.
3. Write a simplified version of the given law text that is easy to understand for everyone. 

---

** RESTRICTIONS

1. Answer in the format specified below. Do not include anything else in your answer. If you need to include additional information, use the `notes` field.
2. The texts for the summary, the simplified text and the notes MUST be in Romanian.
3. Use specific mentions to sections, articles, and paragraphs to justify your answer.

---

** RESPONSE STRUCTURE

Respond only with a JSON code block in the following format. DO NOT INCLUDE ANYTHING ELSE IN YOUR ANSWER.
```json
{
  "law_summary": "",
  "law_simplified": "",
  "articles_summary": "",
  "notes": ""
}
```

** INPUTS

1. Law text:
```law_text
{law_text}
```

2. Article text:
```article_text
{relevant_article}
```
"""

def get_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_gemini_informations_about_law(law_text, relevant_article):
    print(f"[GEMINI][{get_time()}] get info")
    task = TASK_PROMPT.replace("{law_text}", law_text).replace("{relevant_article}", relevant_article)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=task,
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0)
        )
    )
    print(f"[GEMINI][{get_time()}] done request")
    raw_json = extract_code_block(response.text, "json")
    if not raw_json:
        print("Gemini nu a returnat JSON valid.")
        return None
    response = None
    try:
        response = json.loads(raw_json)
    except json.JSONDecodeError as e:
        print("JSON invalid:", e)
        return None
    responses = [response.get('law_summary', ''), response.get('law_simplified', ''), response.get('articles_summary', '')]
    print(f"[GEMINI] notes {response.get('notes', '')}")
    print('\n\n', responses)
    print('\n\n', len(responses))
    return responses

def extract_code_block(text: str, label: str) -> str:
    pattern = rf"```{re.escape(label)}\s*(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return text
    return None

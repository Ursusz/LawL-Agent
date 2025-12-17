from google import genai
from google.genai import types
import os
from .. import config
import json
import datetime
import re
from ..utilities.gemini_utils import get_random_gemini_model, call_gemini_with_retry



client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# Extrage referințele legislative din documentul atașat, găsește legile respective în surse primare pe internet (de exemplu pe site-ul legislatie.just.ro) și extrage fragmentele de lege relevante pentru document, sumarizând elementele cheie. Justifică informațiile extrase prin referințe la surse primare. 
# 2. Write a simplified version of the law text, making it easy to understand for someone unfamiliar with the topic.
#  "simplified_law_text": "",

FULL_LAW_SUMMARY_PROMPT = """
** TASKS:

1. Write a summary for the given law text, covering the most important 5 key aspects.
2. Write a simplified version of the given law text that is easy to understand for everyone. 

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
  "notes": ""
}
```

** INPUTS

1. Law text:
```law_text
{law_text}
```
"""

TARGETED_ARTICLE_SUMMARY_PROMPT = """
** TASKS:

1. Write a summary in plain and easy to understand language for the given articles extracted from a law, explaining their relevance and key points with respect to the given document.

---

** RESTRICTIONS

1. Answer in the format specified below. Do not include anything else in your answer. If you need to include additional information, use the `notes` field.
2. The texts for the summary and the notes MUST be in Romanian.
3. Use specific mentions to sections, articles, and paragraphs to justify your answer.

---

** RESPONSE STRUCTURE

Respond only with a JSON code block in the following format. DO NOT INCLUDE ANYTHING ELSE IN YOUR ANSWER.
```json
{
  "articles_summary": "",
  "notes": ""
}
```

** INPUTS

1. Document text (for context):
```doc_text
{law_text}
```

2. Relevant articles:
```article_text
{relevant_article}
```
"""

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

def get_full_law_summary(law_text):
    """Generate only the full law summary and simplified version (cacheable).
    
    Args:
        law_text: The full text of the law
        
    Returns:
        Dict with 'law_summary' and 'law_simplified', or None on error
    """
    import time
    
    print(f"[GEMINI][{get_time()}] get full law summary")

    if os.environ.get("MOCK_GEMINI", "false").lower() == "true":
        print(f"[GEMINI][{get_time()}] MOCK MODE: Returning mock full law summary")
        return {
            'law_summary': "[MOCK] Aceasta este o rezumare simulată a legii. Legea reglementează aspecte importante privind funcționarea instituțiilor.",
            'law_simplified': "[MOCK] Legea explicată simplu: Trebuie să respecți regulile stabilite pentru a evita sancțiunile."
        }

    task = FULL_LAW_SUMMARY_PROMPT.replace("{law_text}", law_text)
    
    def make_request():
        return client.models.generate_content(
            model=get_random_gemini_model(),
            contents=task,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                max_output_tokens=2048
            )
        )

    response = call_gemini_with_retry(make_request)
    print(f"[GEMINI][{get_time()}] done full law summary request")
    
    if not response or not response.text:
        print("Gemini nu a returnat JSON valid sau a eșuat.")
        return None

    raw_json = extract_code_block(response.text, "json")
    if not raw_json:
        print("Gemini nu a returnat JSON valid.")
        return None
    
    try:
        response_data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        print("JSON invalid:", e)
        return None
    
    result = {
        'law_summary': response_data.get('law_summary', ''),
        'law_simplified': response_data.get('law_simplified', '')
    }
    print(f"[GEMINI] notes {response_data.get('notes', '')}")
    return result
    
    return None

def get_targeted_article_summary(law_text, relevant_article):
    """Generate only the targeted article summary (not cached).
    
    Args:
        law_text: The full text of the law (for context)
        relevant_article: The specific article to summarize
        
    Returns:
        Dict with 'articles_summary', or None on error
    """
    import time
    
    print(f"[GEMINI][{get_time()}] get targeted article summary")

    if os.environ.get("MOCK_GEMINI", "false").lower() == "true":
        print(f"[GEMINI][{get_time()}] MOCK MODE: Returning mock targeted article summary")
        return {
            'articles_summary': "[MOCK] Articolul relevant specifică faptul că termenele de depunere sunt stricte și trebuie respectate conform procedurii."
        }

    task = TARGETED_ARTICLE_SUMMARY_PROMPT.replace("{law_text}", law_text).replace("{relevant_article}", relevant_article)
    
    def make_request():
        return client.models.generate_content(
            model=get_random_gemini_model(),
            contents=task,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                max_output_tokens=2048
            )
        )

    response = call_gemini_with_retry(make_request)
    print(f"[GEMINI][{get_time()}] done targeted article summary request")

    if not response or not response.text:
        print("Gemini nu a returnat JSON valid sau a eșuat.")
        return None
            
    raw_json = extract_code_block(response.text, "json")
    if not raw_json:
        print("Gemini nu a returnat JSON valid.")
        return None
    
    try:
        response_data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        print("JSON invalid:", e)
        return None
    
    result = {
        'articles_summary': response_data.get('articles_summary', '')
    }
    print(f"[GEMINI] notes {response_data.get('notes', '')}")
    return result
    
    return None

def get_gemini_informations_about_law(law_text, relevant_article):
    import time
    
    print(f"[GEMINI][{get_time()}] get info")

    if os.environ.get("MOCK_GEMINI", "false").lower() == "true":
        print(f"[GEMINI][{get_time()}] MOCK MODE: Returning mock info")
        return [
            "[MOCK] Rezumat lege simulat.",
            "[MOCK] Lege simplificată simulată.",
            "[MOCK] Rezumat articole simulat."
        ]

    task = TASK_PROMPT.replace("{law_text}", law_text).replace("{relevant_article}", relevant_article)
    
    def make_request():
        return client.models.generate_content(
            model=get_random_gemini_model(),
            contents=task,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                max_output_tokens=2048
            )
        )

    response = call_gemini_with_retry(make_request)
    print(f"[GEMINI][{get_time()}] done request")

    if not response or not response.text:
        print("Gemini nu a returnat JSON valid sau a eșuat.")
        return None
            
    raw_json = extract_code_block(response.text, "json")
    if not raw_json:
        print("Gemini nu a returnat JSON valid.")
        return None
    
    try:
        response_data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        print("JSON invalid:", e)
        return None
    
    responses = [response_data.get('law_summary', ''), response_data.get('law_simplified', ''), response_data.get('articles_summary', '')]
    print(f"[GEMINI] notes {response_data.get('notes', '')}")
    return responses
    
    return None

def extract_code_block(text: str, label: str) -> str:
    pattern = rf"```{re.escape(label)}\s*(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return text
    return None

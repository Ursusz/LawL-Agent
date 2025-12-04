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

1. Write a summary for the given articles extracted from a law, explaining their relevance and key points.

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

1. Law text (for context):
```law_text
{law_text}
```

2. Article text:
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
    task = FULL_LAW_SUMMARY_PROMPT.replace("{law_text}", law_text)
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=task,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                    max_output_tokens=2048
                )
            )
            print(f"[GEMINI][{get_time()}] done full law summary request")
            
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
            
            result = {
                'law_summary': response.get('law_summary', ''),
                'law_simplified': response.get('law_simplified', '')
            }
            print(f"[GEMINI] notes {response.get('notes', '')}")
            return result
            
        except Exception as e:
            error_str = str(e)
            print(f"[GEMINI] Error on attempt {attempt + 1}: {error_str}")
            
            # Check if it's a rate limit error
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                # Try to parse retry delay from error
                retry_delay = 35  # Default delay
                
                # Try to extract retryDelay from error message
                import re
                delay_match = re.search(r'Please retry in (\d+(?:\.\d+)?)s', error_str)
                if delay_match:
                    retry_delay = float(delay_match.group(1)) + 1  # Add 1 second buffer
                
                if attempt < max_retries - 1:
                    print(f"[GEMINI] Rate limit hit, waiting {retry_delay} seconds before retry...")
                    time.sleep(retry_delay)
                else:
                    print(f"[GEMINI] Max retries reached, giving up")
                    return None
            else:
                # For other errors, don't retry
                return None
    
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
    task = TARGETED_ARTICLE_SUMMARY_PROMPT.replace("{law_text}", law_text).replace("{relevant_article}", relevant_article)
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=task,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                    max_output_tokens=2048
                )
            )
            print(f"[GEMINI][{get_time()}] done targeted article summary request")
            
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
            
            result = {
                'articles_summary': response.get('articles_summary', '')
            }
            print(f"[GEMINI] notes {response.get('notes', '')}")
            return result
            
        except Exception as e:
            error_str = str(e)
            print(f"[GEMINI] Error on attempt {attempt + 1}: {error_str}")
            
            # Check if it's a rate limit error
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                # Try to parse retry delay from error
                retry_delay = 35  # Default delay
                
                # Try to extract retryDelay from error message
                import re
                delay_match = re.search(r'Please retry in (\d+(?:\.\d+)?)s', error_str)
                if delay_match:
                    retry_delay = float(delay_match.group(1)) + 1  # Add 1 second buffer
                
                if attempt < max_retries - 1:
                    print(f"[GEMINI] Rate limit hit, waiting {retry_delay} seconds before retry...")
                    time.sleep(retry_delay)
                else:
                    print(f"[GEMINI] Max retries reached, giving up")
                    return None
            else:
                # For other errors, don't retry
                return None
    
    return None

def get_gemini_informations_about_law(law_text, relevant_article):
    import time
    
    print(f"[GEMINI][{get_time()}] get info")
    task = TASK_PROMPT.replace("{law_text}", law_text).replace("{relevant_article}", relevant_article)
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=task,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                    max_output_tokens=2048
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
            return responses
            
        except Exception as e:
            error_str = str(e)
            print(f"[GEMINI] Error on attempt {attempt + 1}: {error_str}")
            
            # Check if it's a rate limit error
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                # Try to parse retry delay from error
                retry_delay = 35  # Default delay
                
                # Try to extract retryDelay from error message
                import re
                delay_match = re.search(r'Please retry in (\d+(?:\.\d+)?)s', error_str)
                if delay_match:
                    retry_delay = float(delay_match.group(1)) + 1  # Add 1 second buffer
                
                if attempt < max_retries - 1:
                    print(f"[GEMINI] Rate limit hit, waiting {retry_delay} seconds before retry...")
                    time.sleep(retry_delay)
                else:
                    print(f"[GEMINI] Max retries reached, giving up")
                    return None
            else:
                # For other errors, don't retry
                return None
    
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

import datetime
from google import genai
from google.genai import types
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# Extrage referințele legislative din documentul atașat, găsește legile respective în surse primare pe internet (de exemplu pe site-ul legislatie.just.ro) și extrage fragmentele de lege relevante pentru document, sumarizând elementele cheie. Justifică informațiile extrase prin referințe la surse primare. 
# 2. Write a simplified version of the law text, making it easy to understand for someone unfamiliar with the topic.
#  "simplified_law_text": "",
TASK_PROMPT = """
** TASKS:

1. Write a summary for the given law text, covering the most important 5 key aspects.
2. Write a summary for the given articles extracted from the same law.

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

def get_text_summary(text):
    print(f"[GEMINI] get summary")
    PROMPT = "Sumarizeaza, pastrand intreaga esenta si informatie a textului, fara emoticoane, fara stiluri de font(bold, italic), fara '*' sau alte caractere similare:"
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"{PROMPT} {text}"
    )
    return response.text

def get_law_text_simplified(text):
    print(f"[GEMINI] get simplification")
    PROMPT = "Rescrie aceasta lege, sa fie usor de inteles pentru oricine, fara emoticoane, fara stiluri de font(bold, italic), fara explicatii extra, fara text introductiv:"
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"{PROMPT} {text}"
    )
    return response.text

def get_gemini_informations_about_law(law_text, relevant_article):
    print(f"[GEMINI][{get_time()}] get info")
    SUMMARY_PROMPT = "Sumarizeaza, pastrand intreaga esenta si informatie a textului, fara emoticoane, fara stiluri de font(bold, italic), fara '*' sau alte caractere similare:"
    SIMPLIFY_PROMPT = "Rescrie aceasta lege, sa fie usor de inteles pentru oricine, fara emoticoane, fara stiluri de font(bold, italic), fara explicatii extra, fara text introductiv:"
    BREAKUP_PROMPT = "Iti voi da 3 task-uri despartite prin 'question', raspunsurile aferente fiecarui task trebuie despartite de tine prin 'response'. Tokenul 'response' va fi pus DUPA fiecare raspuns, nu inainte"
    first_task = " question " + SUMMARY_PROMPT + law_text
    second_task = " question " + SIMPLIFY_PROMPT + law_text
    third_task = " question  " + SUMMARY_PROMPT + relevant_article
    task = TASK_PROMPT.replace("{law_text}", law_text).replace("{relevant_article}", relevant_article) # BREAKUP_PROMPT + first_task + second_task + third_task
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=task,
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0)
        )
    )
    print(f"[GEMINI][{get_time()}] done request")
    response = json.loads(extract_code_block(response.text, "json")) # .split("response")
    responses = [response["law_summary"], response["articles_summary"]]
    print(f"[GEMINI] notes {response['notes']}")
    return responses


def get_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def extract_code_block(text: str, label: str) -> str:
    """
    Extracts a code block from a string based on its language label.

    This function uses a regular expression to find a block of text
    enclosed by triple backticks (```) and a specific language label.

    Args:
        text (str): The string containing the code block.
        label (str): The language label of the code block (e.g., 'json', 'python').

    Returns:
        str: The content of the code block as a string, or None if no matching
             block is found.
    """
    # Create the regular expression pattern.
    # The pattern looks for:
    # 1. ``` (triple backticks)
    # 2. The provided label (escaped to handle special regex characters)
    # 3. A newline character
    # 4. A capture group (.*?) that non-greedily matches any character, including newlines.
    # 5. ``` (the closing triple backticks)
    # re.DOTALL is used to ensure the '.' matches newline characters.
    pattern = rf"```{re.escape(label)}\n(.*?)```"
    
    # Search for the pattern in the input text.
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        # If a match is found, return the content of the captured group (group 1).
        return match.group(1).strip()
    else:
        # If no match is found, return None.
        return None

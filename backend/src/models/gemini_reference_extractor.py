from google import genai
from google.genai import types
import os
from .. import config
import json
import datetime
import re
from ..utilities.gemini_utils import get_random_gemini_model, call_gemini_with_retry



client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

TASK_PROMPT = """
** PERSONA:
As a lawyer, you are helping a client understand the laws that are relevant to their case. Explain in simple language what the beaurocratic burdens are regarding their document.

** TASK:
Identify ALL implicit or *implied* references (NOT EXPLICIT) to Romanian laws, codes, or regulations in the provided document.
Try to understand what the document is about and what laws it is referring to implicitly from context.
Examples: Codul civil, Codul penal, Codul fiscal, Codul muncii, Codul silvic, Codul administrativ, Codul rutier, Codul vamal, Codul de procedură civilă, Codul de procedură penală, Codul de procedură fiscală.

** RESTRICTIONS:
1. Respond ONLY with a JSON object.
2. The JSON should contain a single key "references" which is a list of strings.
3. If no references are found (unlikely), return an empty list.
4. Do not include explicit references that already appear in the document.
5. Ensure you do not include duplicate references.

** INPUT DOCUMENT:
```
{text}
```

** RESPONSE FORMAT:
```json
{
  "references": [
    "Codul civil",
    "Codul penal"
  ]
}
```
"""

def get_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def extract_code_block(text: str, label: str) -> str:
    pattern = rf"```{re.escape(label)}\s*(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return text
    return None

def extract_implicit_references(text: str) -> list[str]:
    import time
    
    print(f"[GEMINI][{get_time()}] Extracting implicit references")
    
    # Truncate text if it's too long to avoid token limits, though Gemini has a large context window.
    # For extraction, the beginning of the document is usually most relevant, or we might need to chunk it.
    # For now, let's take the first 30000 characters which should cover most use cases.
    truncated_text = text[:30000]
    
    task = TASK_PROMPT.replace("{text}", truncated_text)
    
    if os.environ.get("MOCK_GEMINI", "false").lower() == "true":
        print(f"[GEMINI][{get_time()}] MOCK MODE: Returning mock implicit references")
        return ["Codul civil", "Codul penal", "Legea 31/1990", "Codul mock"]
    
    def make_request():
        return client.models.generate_content(
            model=get_random_gemini_model(),
            contents=task,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                max_output_tokens=2048
            )
        )

    response = call_gemini_with_retry(make_request)
    
    print(f"[GEMINI][{get_time()}] Extraction request done")
    
    if not response or not response.text:
        print("Gemini returned empty response or failed")
        return []

    # Since we requested JSON mime type, we might get raw JSON directly or wrapped in markdown
    raw_json = extract_code_block(response.text, "json")
    if not raw_json:
        raw_json = response.text

    try:
        data = json.loads(raw_json)
        references = data.get("references", [])
        
        # Ensure all items are strings
        references = [str(ref) for ref in references if isinstance(ref, str)]
        
        print(f"[GEMINI] Found references: {references}")
        return references
    except json.JSONDecodeError:
        print(f"[GEMINI] Failed to decode JSON response")
        return []
    
    return []

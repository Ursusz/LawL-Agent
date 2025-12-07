from google import genai
from google.genai import types
import os
from .. import config
import json
import datetime
import re
from ..utilities.gemini_utils import get_random_gemini_model



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
        return ["Codul civil", "Codul penal", "Legea 31/1990"]
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                # model="gemini-2.0-flash-lite",
                model=get_random_gemini_model(),
                contents=task,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    max_output_tokens=2048
                )
            )
            
            print(f"[GEMINI][{get_time()}] Extraction request done")
            
            if not response.text:
                print("Gemini returned empty response")
                return []

            # Since we requested JSON mime type, we might get raw JSON directly or wrapped in markdown
            raw_json = extract_code_block(response.text, "json")
            if not raw_json:
                raw_json = response.text

            data = json.loads(raw_json)
            references = data.get("references", [])
            
            # Ensure all items are strings
            references = [str(ref) for ref in references if isinstance(ref, str)]
            
            print(f"[GEMINI] Found references: {references}")
            return references
            
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
                    return []
            else:
                # For other errors, return empty list
                print(f"[GEMINI] Non-rate-limit error, returning empty list")
                return []
    
    return []

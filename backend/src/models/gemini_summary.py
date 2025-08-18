from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def get_text_summary(text):
    PROMPT = "Sumarizeaza, fara emoticoane, fara stiluri de font(bold, italic):"
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"{PROMPT} {text}"
    )
    return response.text

def get_law_text_simplified(text):
    PROMPT = "Rescrie aceasta lege, sa fie usor de inteles pentru oricine, fara emoticoane, fara stiluri de font(bold, italic), fara explicatii extra, fara text introductiv:"
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"{PROMPT} {text}"
    )
    return response.text
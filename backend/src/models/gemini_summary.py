from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def get_text_summary(text):
    PROMPT = "Sumarizeaza, pastrand intreaga esenta si informatie a textului, fara emoticoane, fara stiluri de font(bold, italic), fara '*' sau alte caractere similare:"
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

def get_gemini_informations_about_law(law_text, relevant_article):
    SUMMARY_PROMPT = "Sumarizeaza, pastrand intreaga esenta si informatie a textului, fara emoticoane, fara stiluri de font(bold, italic), fara '*' sau alte caractere similare:"
    SIMPLIFY_PROMPT = "Rescrie aceasta lege, sa fie usor de inteles pentru oricine, fara emoticoane, fara stiluri de font(bold, italic), fara explicatii extra, fara text introductiv:"
    BREAKUP_PROMPT = "Iti voi da 3 task-uri despartite prin 'question', raspunsurile aferente fiecarui task trebuie despartite de tine prin 'response'. Tokenul 'response' va fi pus DUPA fiecare raspuns, nu inainte"
    first_task = " question " + SUMMARY_PROMPT + law_text
    second_task = " question " + SIMPLIFY_PROMPT + law_text
    third_task = " question  " + SUMMARY_PROMPT + relevant_article
    task = BREAKUP_PROMPT + first_task + second_task + third_task
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=task,
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0)
        )
    )
    responses = response.text.split("response")
    return responses
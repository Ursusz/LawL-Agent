from odf.opendocument import load as odf_load
from odf.text import P
from docx import Document
import io, os
from PyPDF2 import PdfReader
import subprocess

def extract_text_odt(file_content):
    doc = odf_load(io.BytesIO(file_content))
    paragraphs = doc.getElementsByType(P)
    return '\n'.join([p.firstChild.data if p.firstChild else '' for p in paragraphs])

def extract_text_docx(file_content):
    doc = Document(io.BytesIO(file_content))
    return '\n'.join([p.text for p in doc.paragraphs])

def extract_text_txt(file_content):
    return file_content.decode('utf-8')

def extract_text_pdf(file_content):
    pdf_file = io.BytesIO(file_content)

    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""

    return text

def extract_text_doc(file_content):
    try:
        result = subprocess.run(
            ['antiword', '-'],
            input=file_content,
            capture_output=True,
            text=False,
            check=True,
        )
        text_output = result.stdout.decode('utf-8', errors='ignore')
        stripped_text = ""
        for row in text_output.split('\n'):
            stripped_text += row or ""
        return stripped_text
    except subprocess.CalledProcessError as e:
        print(f"Error while processing file .doc: {e}")
        return ""
    except Exception as e:
        print(f"Unknown error occured: {e}")
        return ""

async def parse_file(filename, file_content):
    ext = os.path.splitext(filename)[1].lower()

    if ext == '.odt':
        return extract_text_odt(file_content)
    elif ext == '.docx':
        return extract_text_docx(file_content)
    elif ext == '.txt':
        return extract_text_txt(file_content)
    elif ext == '.doc':
        return extract_text_doc(file_content)
    elif ext == '.pdf':
        return extract_text_pdf(file_content)
    else:
        raise ValueError(f"Tip de fisier nesuportat: {ext}")
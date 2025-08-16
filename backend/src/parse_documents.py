from odf.opendocument import load as odf_load
from odf.text import P
from docx import Document
import io, os

def extract_text_odt(file_content):
    doc = odf_load(io.BytesIO(file_content))
    paragraphs = doc.getElementsByType(P)
    return '\n'.join([p.firstChild.data if p.firstChild else '' for p in paragraphs])

def extract_text_docx(file_content):
    doc = Document(io.BytesIO(file_content))
    return '\n'.join([p.text for p in doc.paragraphs])

def extract_text_txt(file_content):
    return file_content.decode('utf-8')
    
async def parse_file(filename, file_content):
    ext = os.path.splitext(filename)[1].lower()

    if ext == '.odt':
        return extract_text_odt(file_content)
    elif ext == '.docx':
        return extract_text_docx(file_content)
    elif ext == '.txt':
        return extract_text_txt(file_content)
    else:
        raise ValueError(f"Tip de fisier nesuportat: {ext}")
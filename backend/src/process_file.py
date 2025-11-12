from fastapi import UploadFile
from typing import List, Dict, Any
from . import parse_documents
from . import extract_references
from . import search_laws


async def process_file(file: UploadFile) -> Dict[str, Any]:
    try:
        document_text = await parse_documents.parse_file(file.filename, await file.read())
        references = extract_references.extract_law_references(document_text)
        laws = search_laws.find_laws(references, document_text)
        results = {
            "filename": file.filename,
            "references": references,
            "law_details": laws
        }
    except Exception as e:
        error_msg = str(e)
        if "503" in error_msg or "UNAVAILABLE" in error_msg:
            frontend_err = "The Gemini AI service is temporarily unavailable due to high demand. Please try again in a few moments."
        elif error_msg in ["law_summary", "law_simplified", "articles_summary", "notes"]:
            frontend_err = "Gemini AI service failed to create the correct JSON format."
        else:
            frontend_err = f"Error processing file: {error_msg}"
        results = {
            "filename": file.filename,
            "error": frontend_err
        }
    return results
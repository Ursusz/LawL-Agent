from fastapi import UploadFile
from typing import List, Dict, Any
import parse_documents, extract_references, search_laws

async def process_file(file: UploadFile) -> Dict[str, Any]:
    try:
        document_text = await parse_documents.parse_file(file.filename, await file.read())
        references = extract_references.extract_law_references(document_text)
        law_details = search_laws.find_laws(references, document_text)
        # print(law_details)
        # excerpt = summarize.create_summary(text)
        results = {
            "filename": file.filename,
            "references": references,
            "law_details": law_details,
            # "excerpt": excrpt
        }

    except Exception as e:
        results = {
            "filename": file.filename,
            "error": f"Failed to process file: {e}"
        }

    return results
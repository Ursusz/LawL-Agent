from fastapi import UploadFile
from typing import List, Dict, Any
from . import parse_documents
from . import extract_references
from . import search_laws
from .models import gemini_reference_extractor
from .utilities import standardize_law_title


async def process_file(file: UploadFile) -> Dict[str, Any]:
    try:
        document_text = await parse_documents.parse_file(file.filename, await file.read())
        print(document_text)
        
        # 1. Regex-based extraction
        regex_references = extract_references.extract_law_references(document_text)
        print(f"Regex references: {regex_references}")
        
        # 2. LLM-based implicit extraction
        implicit_references = gemini_reference_extractor.extract_implicit_references(document_text)
        print(f"Implicit references: {implicit_references}")
        
        # 3. Merge and standardize
        all_references = set(regex_references)
        for ref in implicit_references:
            std_ref = standardize_law_title.standardize_law_title(ref)
            if std_ref:
                # Re-construct standard string format as in extract_references.py
                # This logic should ideally be centralized, but duplicating for now to match existing pattern
                law_reference_standard = ''
                if len(std_ref) == 3:
                    tip_act, nr_act, an_act = std_ref
                    law_reference_standard = f'{tip_act}_{nr_act}_{an_act}'
                elif len(std_ref) == 4:
                    tip_act, nr_act1, nr_act2, an_act = std_ref
                    law_reference_standard = f'{tip_act}_{nr_act1}_{nr_act2}_{an_act}'
                
                if law_reference_standard:
                    all_references.add(law_reference_standard)
            else:
                # Fallback: if standardization fails, use the original reference
                # This allows searching for things like "Codul Fiscal" directly
                # Sanitize: keep alnum, space, /; then replace space, / with _; truncate to 100
                import re
                ref = re.sub(r"[ăâ]", "a", ref)
                ref = re.sub(r"[î]", "i", ref)
                ref = re.sub(r"[șş]", "s", ref)
                ref = re.sub(r"[țţ]", "t", ref)
                ref = re.sub(r"[ĂÂ]", "A", ref)
                ref = re.sub(r"[Î]", "I", ref)
                ref = re.sub(r"[ȘŞ]", "S", ref)
                ref = re.sub(r"[ȚŢ]", "T", ref)
                sanitized_ref = re.sub(r'[^a-zA-Z0-9 _/]', '', ref)
                sanitized_ref = re.sub(r'[ /]', '_', sanitized_ref)
                sanitized_ref = sanitized_ref[:100]
                all_references.add(sanitized_ref)
        
        references = list(all_references)
        print(f"Final merged references: {references}")
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
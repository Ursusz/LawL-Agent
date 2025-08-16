from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import List

import parse_documents
import extract_references
import search_laws
import summarize

app = FastAPI()

origins = [
    "http://localhost:3000", #frontend
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/search")
async def search_laws_in_documents(files: List[UploadFile] = File(...)):
    results = []

    for file in files:
        try:
            text = await parse_documents.parse_file(file.filename, await file.read())
            references = extract_references.extract_law_references(text)
            law_details = search_laws.find_laws(references)
            # excerpt = summarize.create_summary(text)
            results.append({
                "filename": file.filename,
                "references": references,
                "law_details": law_details,
                # "excerpt": excrpt
            })

        except Exception as e:
            results.append({
                "filename": file.filename,
                "error": f"Failed to process file: {e}"
            })

    return results

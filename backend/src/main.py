from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from . import process_file

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
        result = await process_file.process_file(file)
        results.append(result)

    return results
from fastapi import FastAPI, UploadFile, File, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import List, Optional
import uuid
import json

from . import process_file
from .progress_tracker import progress_tracker

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

@app.get("/progress/{session_id}")
async def stream_progress(session_id: str):
    """Stream progress events for a specific session using Server-Sent Events."""
    
    async def event_generator():
        async for event in progress_tracker.get_events(session_id):
            # Format as SSE
            yield f"data: {json.dumps(event)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )

@app.post("/search")
async def search_laws_in_documents(
    files: List[UploadFile] = File(...),
    x_session_id: Optional[str] = Header(None)
):
    """Process uploaded files and search for law references.
    
    If X-Session-ID header is provided, progress events will be streamed
    to the /progress/{session_id} endpoint.
    """
    # Generate session ID if not provided
    session_id = x_session_id or str(uuid.uuid4())
    
    # Create session for progress tracking
    progress_tracker.create_session(session_id)
    
    results = []
    
    for file in files:
        result = await process_file.process_file(file, session_id)
        results.append(result)
    
    # Emit completion event
    await progress_tracker.emit_processing_complete(session_id)
    
    return results
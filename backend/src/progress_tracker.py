import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional
from collections import defaultdict


class ProgressTracker:
    """Manages progress events for document processing sessions."""
    
    def __init__(self):
        # Store queues for each session
        self._queues: Dict[str, asyncio.Queue] = {}
        self._sessions: Dict[str, Dict[str, Any]] = defaultdict(dict)
    
    def create_session(self, session_id: str):
        """Create a new session for tracking progress."""
        if session_id not in self._queues:
            self._queues[session_id] = asyncio.Queue()
            self._sessions[session_id] = {
                'created_at': datetime.now().isoformat(),
                'status': 'active'
            }
    
    def close_session(self, session_id: str):
        """Mark a session as complete."""
        if session_id in self._sessions:
            self._sessions[session_id]['status'] = 'complete'
    
    async def emit(self, session_id: str, event_type: str, data: Dict[str, Any]):
        """Emit a progress event for a specific session."""
        if session_id not in self._queues:
            self.create_session(session_id)
        
        event = {
            'type': event_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        await self._queues[session_id].put(event)
    
    async def get_events(self, session_id: str):
        """Generator that yields events for a session."""
        if session_id not in self._queues:
            self.create_session(session_id)
        
        queue = self._queues[session_id]
        
        try:
            while True:
                # Wait for next event with timeout
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield event
                    
                    # If this is a completion event, break
                    if event['type'] == 'processing_complete':
                        break
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield {'type': 'keepalive', 'timestamp': datetime.now().isoformat()}
        finally:
            # Cleanup
            if session_id in self._queues:
                del self._queues[session_id]
            if session_id in self._sessions:
                del self._sessions[session_id]
    
    # Convenience methods for common events
    
    async def emit_reference_extraction_start(self, session_id: str, extraction_type: str):
        """Emit event when starting reference extraction."""
        await self.emit(session_id, 'reference_extraction_start', {
            'extraction_type': extraction_type  # 'explicit' or 'implicit'
        })
    
    async def emit_reference_extraction_complete(self, session_id: str, extraction_type: str, references: list):
        """Emit event when reference extraction completes."""
        await self.emit(session_id, 'reference_extraction_complete', {
            'extraction_type': extraction_type,
            'references': references,
            'count': len(references)
        })
    
    async def emit_reference_processing_start(self, session_id: str, reference: str):
        """Emit event when starting to process a reference."""
        await self.emit(session_id, 'reference_processing_start', {
            'reference': reference
        })
    
    async def emit_reference_stage_update(self, session_id: str, reference: str, stage: str, cached: bool = False):
        """Emit event for a processing stage update.
        
        Stages:
        - checking_cache
        - cache_hit / cache_miss
        - fetching_law_text
        - generating_law_summary
        - generating_article_summary
        - generating_simplified
        """
        await self.emit(session_id, 'reference_stage_update', {
            'reference': reference,
            'stage': stage,
            'cached': cached
        })
    
    async def emit_reference_complete(self, session_id: str, reference: str, success: bool = True, error: Optional[str] = None):
        """Emit event when reference processing completes."""
        await self.emit(session_id, 'reference_complete', {
            'reference': reference,
            'success': success,
            'error': error
        })
    
    async def emit_processing_complete(self, session_id: str):
        """Emit event when entire processing is complete."""
        await self.emit(session_id, 'processing_complete', {})
        self.close_session(session_id)


# Global instance
progress_tracker = ProgressTracker()

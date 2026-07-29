"""Server-Sent Events (SSE) endpoints - DEPRECATED.

Use WebSocket for real-time updates instead.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/pending/stream")
async def stream_pending():
    """Stream pending jobs updates via SSE. DEPRECATED."""
    return {"status": "deprecated", "message": "Use WebSocket for real-time updates"}


@router.get("/pending-companies/stream")
async def stream_pending_companies():
    """Stream pending companies updates via SSE. DEPRECATED."""
    return {"status": "deprecated", "message": "Use WebSocket for real-time updates"}

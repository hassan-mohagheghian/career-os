"""Server-Sent Events (SSE) endpoints for real-time data streaming."""

import asyncio
import json
import time

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import sqlite3

from dependencies import get_db

router = APIRouter()


async def _stream_pending_jobs(db_factory):
    """Stream pending jobs updates via SSE."""
    last_hash = ""
    while True:
        db = db_factory()
        try:
            rows = db.execute(
                "SELECT * FROM pending_jobs ORDER BY created_at DESC"
            ).fetchall()
            data = json.dumps([dict(r) for r in rows], ensure_ascii=False)
            current_hash = str(hash(data))
            if current_hash != last_hash:
                last_hash = current_hash
                yield f"data: {data}\n\n"
        finally:
            db.close()
        await asyncio.sleep(2)


async def _stream_pending_companies(db_factory):
    """Stream pending companies updates via SSE."""
    last_hash = ""
    while True:
        db = db_factory()
        try:
            rows = db.execute(
                "SELECT * FROM pending_companies ORDER BY created_at DESC"
            ).fetchall()
            data = json.dumps([dict(r) for r in rows], ensure_ascii=False)
            current_hash = str(hash(data))
            if current_hash != last_hash:
                last_hash = current_hash
                yield f"data: {data}\n\n"
        finally:
            db.close()
        await asyncio.sleep(2)


@router.get("/pending/stream")
async def stream_pending(db: sqlite3.Connection = Depends(get_db)):
    """Stream pending jobs updates via SSE."""
    def db_factory():
        import sqlite3
        from config import DB_PATH
        conn = sqlite3.connect(DB_PATH, timeout=5)
        conn.row_factory = sqlite3.Row
        return conn

    return StreamingResponse(
        _stream_pending_jobs(db_factory),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/pending-companies/stream")
async def stream_pending_companies(db: sqlite3.Connection = Depends(get_db)):
    """Stream pending companies updates via SSE."""
    def db_factory():
        import sqlite3
        from config import DB_PATH
        conn = sqlite3.connect(DB_PATH, timeout=5)
        conn.row_factory = sqlite3.Row
        return conn

    return StreamingResponse(
        _stream_pending_companies(db_factory),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )

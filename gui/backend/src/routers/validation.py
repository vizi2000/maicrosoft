"""Validation router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from fastapi import WebSocket

router = APIRouter()

@router.post("/validate")
async def validate_plan(db: AsyncSession = Depends(get_db)):
    """Handler for POST /validate."""
    # TODO: Implement validate_plan
    return {"message": "Not implemented"}


@router.websocket("/ws/validate")
async def validation_stream(websocket: WebSocket):
    """WebSocket handler for /ws/validate."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            # TODO: Implement validation_stream
            await websocket.send_json({"status": "received"})
    except Exception:
        pass



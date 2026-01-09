"""Compile router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db

router = APIRouter()

@router.post("/compile")
async def compile_plan(db: AsyncSession = Depends(get_db)):
    """Handler for POST /compile."""
    # TODO: Implement compile_plan
    return {"message": "Not implemented"}



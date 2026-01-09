"""Github router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db

router = APIRouter()

@router.post("/analyze/github")
async def analyze_github_repo(db: AsyncSession = Depends(get_db)):
    """Handler for POST /analyze/github."""
    # TODO: Implement analyze_github_repo
    return {"message": "Not implemented"}



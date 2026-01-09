"""Templates router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db

router = APIRouter()

@router.get("/templates")
async def list_templates(db: AsyncSession = Depends(get_db)):
    """Handler for GET /templates."""
    # TODO: Implement list_templates
    return {"message": "Not implemented"}


@router.get("/templates/{id}")
async def get_template(db: AsyncSession = Depends(get_db)):
    """Handler for GET /templates/{id}."""
    # TODO: Implement get_template
    return {"message": "Not implemented"}



"""Primitives router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db

router = APIRouter()

@router.get("/primitives")
async def list_primitives(db: AsyncSession = Depends(get_db)):
    """Handler for GET /primitives."""
    # TODO: Implement list_primitives
    return {"message": "Not implemented"}


@router.get("/primitives/{id}")
async def get_primitive(db: AsyncSession = Depends(get_db)):
    """Handler for GET /primitives/{id}."""
    # TODO: Implement get_primitive
    return {"message": "Not implemented"}


@router.get("/primitives/search")
async def search_primitives(db: AsyncSession = Depends(get_db)):
    """Handler for GET /primitives/search."""
    # TODO: Implement search_primitives
    return {"message": "Not implemented"}



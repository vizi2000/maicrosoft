"""Secrets router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db

router = APIRouter()

@router.get("/secrets")
async def list_secrets(db: AsyncSession = Depends(get_db)):
    """Handler for GET /secrets."""
    # TODO: Implement list_secrets
    return {"message": "Not implemented"}


@router.post("/secrets")
async def create_secret(db: AsyncSession = Depends(get_db)):
    """Handler for POST /secrets."""
    # TODO: Implement create_secret
    return {"message": "Not implemented"}


@router.delete("/secrets/{id}")
async def delete_secret(db: AsyncSession = Depends(get_db)):
    """Handler for DELETE /secrets/{id}."""
    # TODO: Implement delete_secret
    return {"message": "Not implemented"}



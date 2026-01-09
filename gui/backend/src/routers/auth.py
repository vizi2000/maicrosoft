"""Auth router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db

router = APIRouter()

@router.post("/auth/register")
async def register_user(db: AsyncSession = Depends(get_db)):
    """Handler for POST /auth/register."""
    # TODO: Implement register_user
    return {"message": "Not implemented"}


@router.post("/auth/login")
async def login_user(db: AsyncSession = Depends(get_db)):
    """Handler for POST /auth/login."""
    # TODO: Implement login_user
    return {"message": "Not implemented"}


@router.post("/auth/refresh")
async def refresh_token(db: AsyncSession = Depends(get_db)):
    """Handler for POST /auth/refresh."""
    # TODO: Implement refresh_token
    return {"message": "Not implemented"}


@router.get("/auth/me")
async def get_current_user(db: AsyncSession = Depends(get_db)):
    """Handler for GET /auth/me."""
    # TODO: Implement get_current_user
    return {"message": "Not implemented"}



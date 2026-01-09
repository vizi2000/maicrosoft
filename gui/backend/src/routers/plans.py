"""Plans router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db

router = APIRouter()

@router.get("/plans")
async def list_plans(db: AsyncSession = Depends(get_db)):
    """Handler for GET /plans."""
    # TODO: Implement list_plans
    return {"message": "Not implemented"}


@router.post("/plans")
async def create_plan(db: AsyncSession = Depends(get_db)):
    """Handler for POST /plans."""
    # TODO: Implement create_plan
    return {"message": "Not implemented"}


@router.get("/plans/{id}")
async def get_plan(db: AsyncSession = Depends(get_db)):
    """Handler for GET /plans/{id}."""
    # TODO: Implement get_plan
    return {"message": "Not implemented"}


@router.put("/plans/{id}")
async def update_plan(db: AsyncSession = Depends(get_db)):
    """Handler for PUT /plans/{id}."""
    # TODO: Implement update_plan
    return {"message": "Not implemented"}


@router.delete("/plans/{id}")
async def delete_plan(db: AsyncSession = Depends(get_db)):
    """Handler for DELETE /plans/{id}."""
    # TODO: Implement delete_plan
    return {"message": "Not implemented"}


@router.get("/plans/{id}/versions")
async def list_versions(db: AsyncSession = Depends(get_db)):
    """Handler for GET /plans/{id}/versions."""
    # TODO: Implement list_versions
    return {"message": "Not implemented"}


@router.post("/plans/{id}/versions")
async def create_version(db: AsyncSession = Depends(get_db)):
    """Handler for POST /plans/{id}/versions."""
    # TODO: Implement create_version
    return {"message": "Not implemented"}



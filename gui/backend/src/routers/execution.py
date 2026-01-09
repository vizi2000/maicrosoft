"""Execution router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db

router = APIRouter()

@router.post("/plans/{id}/run")
async def execute_plan(db: AsyncSession = Depends(get_db)):
    """Handler for POST /plans/{id}/run."""
    # TODO: Implement execute_plan
    return {"message": "Not implemented"}


@router.get("/runs")
async def list_runs(db: AsyncSession = Depends(get_db)):
    """Handler for GET /runs."""
    # TODO: Implement list_runs
    return {"message": "Not implemented"}


@router.get("/runs/{id}")
async def get_run(db: AsyncSession = Depends(get_db)):
    """Handler for GET /runs/{id}."""
    # TODO: Implement get_run
    return {"message": "Not implemented"}



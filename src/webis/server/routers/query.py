"""
Query API router.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    mode: str = "hybrid" # hybrid, vector, keyword

@router.post("/")
async def search_knowledge(request: QueryRequest):
    """
    Search the knowledge base.
    """
    return {"results": []}

"""
Task management API router.
"""

from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult
from webis.core.celery_app import celery_app

router = APIRouter()

@router.get("/{task_id}")
async def get_task_status(task_id: str):
    """
    Get the status of a background task.
    """
    task_result = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None
    }
    
    if task_result.state == 'PROCESSING':
        response.update(task_result.info or {})
        
    return response

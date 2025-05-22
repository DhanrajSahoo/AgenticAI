from fastapi import APIRouter, HTTPException, Depends
from typing import List
import logging

from schemas.tools_schema import ToolDefinition
from services import tool_service

router = APIRouter(
    prefix="/tools",
    tags=["Tools"]
)
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[ToolDefinition])
async def api_list_available_tools():
    try:
        return tool_service.list_available_tools()
    except Exception as e:
        logger.error(f"Error listing tools: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list tools.")
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
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

class ToolRequest(BaseModel):
    id: str

@router.post("/tool-name")
# async def record_audio(request: RecordRequest):
async def tool_instance(request:ToolRequest):
    try:
        #res = tool_service.list_tool_instance(request.id)
        tool_config = tool_service.list_tool_instance(request.id)
        if not tool_config:
            raise HTTPException(status_code=404, detail=f"No tool found with id '{request.id}'")

        tool_class = tool_config["class"]

        return {
            "id": request.id,
            "name": tool_config["name"],
            "description": tool_config["description"],
            "class_name": tool_class.__name__,
            "parameters_schema": tool_config["parameters_schema"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
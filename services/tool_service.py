from typing import List
from schemas.tools_schema import ToolDefinition
from tool_registry.registry import get_all_tool_definitions, get_tool_instance, get_tool_instance_id


def list_available_tools() -> List[ToolDefinition]:
    return get_all_tool_definitions()

def list_tool_instance(id):
    return get_tool_instance_id(id)
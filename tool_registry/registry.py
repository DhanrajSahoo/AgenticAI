from typing import List, Dict, Any, Optional
from schemas.tools_schema import ToolDefinition, ToolParameterDetail
from .definitions import PREDEFINED_TOOLS_CONFIG
import os


def get_all_tool_definitions() -> List[ToolDefinition]:
    defs = []
    for tool_id, config in PREDEFINED_TOOLS_CONFIG.items():
        param_schema_typed: Optional[Dict[str, ToolParameterDetail]] = None
        if config.get("parameters_schema"):
            param_schema_typed = {
                k: ToolParameterDetail(**v) for k, v in config["parameters_schema"].items()
            }

        defs.append(ToolDefinition(
            id=tool_id,
            name=config["name"],
            description=config["description"],
            parameters_schema=param_schema_typed
        ))
    return defs


def get_tool_instance(tool_id: str, config_params: Optional[Dict[str, Any]] = None) -> Any:
    config = PREDEFINED_TOOLS_CONFIG.get(tool_id)
    if not config:
        raise ValueError(f"Tool with id '{tool_id}' not found in registry.")

    ToolClass = config["class"]

    # Prepare init_kwargs from config_params if provided and tool supports them
    init_kwargs = {}
    if config_params:
        if tool_id == "website_scraper" and "website_url" in config_params and config_params["website_url"]:
            init_kwargs["website_url"] = config_params["website_url"]

        if tool_id == "github_search_tool":
            if "github_repo" in config_params and config_params["github_repo"]:
                init_kwargs["github_repo"] = config_params["github_repo"]
            if "content_types" in config_params and config_params["content_types"]:
                ct_str = config_params["content_types"]
                init_kwargs["content_types"] = [s.strip() for s in ct_str.split(',')] if isinstance(ct_str,
                                                                                                    str) else ct_str

    try:
        if init_kwargs:
            return ToolClass(**init_kwargs)
        return ToolClass()
    except Exception as e:
        print(f"Error instantiating tool '{tool_id}' with params {init_kwargs}: {e}")
        raise RuntimeError(
            f"Failed to instantiate tool '{tool_id}'. Ensure API keys (e.g., SERPER_API_KEY, OPENAI_API_KEY) are set as environment variables. Tool init error: {e}"
        ) from e

def get_tool_instance_id(tool_id):
    config = PREDEFINED_TOOLS_CONFIG.get(tool_id)
    return config
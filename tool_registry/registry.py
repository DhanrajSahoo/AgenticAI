import inspect
from typing import List, Dict, Any, Optional, Union

from schemas.tools_schema import ToolDefinition, ToolParameterDetail
from .definitions import PREDEFINED_TOOLS_CONFIG

_NUMERIC_ID_TO_STRING_ID_MAP: Optional[Dict[int, str]] = None
_STRING_ID_TO_NUMERIC_ID_MAP: Optional[Dict[str, int]] = None


def _build_tool_id_maps():
    """Builds the mapping between numeric IDs and string IDs."""
    global _NUMERIC_ID_TO_STRING_ID_MAP, _STRING_ID_TO_NUMERIC_ID_MAP
    if _NUMERIC_ID_TO_STRING_ID_MAP is not None:
        return

    _NUMERIC_ID_TO_STRING_ID_MAP = {}
    _STRING_ID_TO_NUMERIC_ID_MAP = {}

    sorted_tool_string_ids = sorted(PREDEFINED_TOOLS_CONFIG.keys())

    for i, tool_string_id in enumerate(sorted_tool_string_ids):
        numeric_id = i + 1
        _NUMERIC_ID_TO_STRING_ID_MAP[numeric_id] = tool_string_id
        _STRING_ID_TO_NUMERIC_ID_MAP[tool_string_id] = numeric_id


def get_string_id_from_numeric_id(numeric_id_from_ui: int) -> Optional[str]:
    """Converts a numeric ID (as sent by UI) back to the internal string ID."""
    _build_tool_id_maps()
    return _NUMERIC_ID_TO_STRING_ID_MAP.get(numeric_id_from_ui) if _NUMERIC_ID_TO_STRING_ID_MAP else None


def get_all_tool_definitions() -> List[ToolDefinition]:
    """Generates tool definitions for the API, including a runtime numeric_id."""
    _build_tool_id_maps()
    defs = []

    sorted_tool_string_ids = sorted(PREDEFINED_TOOLS_CONFIG.keys())

    for tool_string_id in sorted_tool_string_ids:
        config = PREDEFINED_TOOLS_CONFIG[tool_string_id]
        numeric_id = _STRING_ID_TO_NUMERIC_ID_MAP.get(tool_string_id) if _STRING_ID_TO_NUMERIC_ID_MAP else None
        if numeric_id is None:
            raise RuntimeError(f"Could not determine numeric ID for tool: {tool_string_id}")

        param_schema_typed: Optional[Dict[str, ToolParameterDetail]] = None
        if config.get("parameters_schema"):
            param_schema_typed = {
                k: ToolParameterDetail(**v) for k, v in config["parameters_schema"].items()
            }

        class_obj = config.get("class")
        class_name_str = class_obj.__name__ if class_obj else None

        defs.append(ToolDefinition(
            numeric_id=numeric_id,
            original_id=tool_string_id,
            name=config["name"],
            description=config["description"],
            class_name=class_name_str,
            parameters_schema=param_schema_typed
        ))
    return defs


def get_tool_instance(
        tool_id_from_workflow: Union[str, int],
        config_params: Optional[Dict[str, Any]] = None
) -> Any:
    _build_tool_id_maps()

    actual_tool_string_id: Optional[str] = None
    if isinstance(tool_id_from_workflow, int):
        actual_tool_string_id = get_string_id_from_numeric_id(tool_id_from_workflow)
        if not actual_tool_string_id:
            raise ValueError(f"Invalid numeric tool ID '{tool_id_from_workflow}' received. No matching tool found.")
    elif isinstance(tool_id_from_workflow, str):
        if tool_id_from_workflow not in PREDEFINED_TOOLS_CONFIG:
            try:
                numeric_id_attempt = int(tool_id_from_workflow)
                actual_tool_string_id = get_string_id_from_numeric_id(numeric_id_attempt)
                if not actual_tool_string_id:
                    raise ValueError(f"Tool ID string '{tool_id_from_workflow}' is not a valid tool identifier "
                                     f"and could not be mapped from a numeric ID.")
            except ValueError:
                raise ValueError(f"Tool ID string '{tool_id_from_workflow}' is not a valid tool identifier.")
        else:
            actual_tool_string_id = tool_id_from_workflow
    else:
        raise TypeError(f"tool_id_from_workflow must be str or int, got {type(tool_id_from_workflow)}")

    config_from_registry = PREDEFINED_TOOLS_CONFIG.get(actual_tool_string_id)
    if not config_from_registry:
        raise ValueError(
            f"Tool with mapped string id '{actual_tool_string_id}' not found in registry (this should not happen).")

    ToolClass = config_from_registry["class"]
    init_kwargs: Dict[str, Any] = {}
    if config_params:
        init_kwargs.update(config_params)

    if actual_tool_string_id == "serper_dev_tool" and "serper_key" in init_kwargs:
        init_kwargs["serper_api_key"] = init_kwargs.pop("serper_key")

    try:
        return ToolClass(**init_kwargs)
    except Exception as e:
        expected_params_info = ""
        if hasattr(ToolClass, "__init__"):
            try:
                sig = inspect.signature(ToolClass.__init__)
                expected_params_info = f"Expected constructor parameters for {ToolClass.__name__}: {sig}."
            except Exception:
                expected_params_info = f"Could not inspect constructor parameters for {ToolClass.__name__}."

        raise RuntimeError(
            f"Failed to instantiate tool '{actual_tool_string_id}'. "
            f"Provided config_params were: {init_kwargs}. "
            f"{expected_params_info} "
            f"Original tool init error: {e}"
        ) from e

def get_tool_instance_id(tool_id):
    config = PREDEFINED_TOOLS_CONFIG.get(tool_id)
    return config
import inspect
from typing import List, Dict, Any, Optional, Union
import logging

from schemas.tools_schema import ToolDefinition, ToolParameterDetail
from .definitions import PREDEFINED_TOOLS_CONFIG
from services.aws_services import CloudWatchLogHandler

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = CloudWatchLogHandler('agentic-ai', 'agentic-ai')
logger.addHandler(handler)

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
    logger.info(f"PREDEFINED_TOOLS_CONFIG{PREDEFINED_TOOLS_CONFIG}")

    sorted_tool_string_ids = sorted(PREDEFINED_TOOLS_CONFIG.keys())

    logger.info(f"sorted_tool_string_ids: {sorted_tool_string_ids}")

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

        logger.info(f"Config from tools : {config}")

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
            raise ValueError(f"Invalid numeric tool ID '{tool_id_from_workflow}' received.")
    elif isinstance(tool_id_from_workflow, str):
        if tool_id_from_workflow in PREDEFINED_TOOLS_CONFIG:
            actual_tool_string_id = tool_id_from_workflow
        else:
            try:
                numeric_id = int(tool_id_from_workflow)
                actual_tool_string_id = get_string_id_from_numeric_id(numeric_id)
                if not actual_tool_string_id:
                    raise ValueError(f"Invalid tool ID string '{tool_id_from_workflow}'")
            except ValueError:
                raise ValueError(f"Tool ID string '{tool_id_from_workflow}' is not a valid identifier.")
    else:
        raise TypeError(f"tool_id_from_workflow must be str or int, got {type(tool_id_from_workflow)}")

    config_from_registry = PREDEFINED_TOOLS_CONFIG.get(actual_tool_string_id)
    if not config_from_registry:
        raise ValueError(f"Tool '{actual_tool_string_id}' not found in registry.")

    ToolClass = config_from_registry["class"]
    init_kwargs: Dict[str, Any] = config_params or {}

    # Safely check if ToolClass accepts kwargs (i.e., a config-enabled tool)
    try:
        sig = inspect.signature(ToolClass.__init__)
        accepts_kwargs = any(
            param.kind in [param.VAR_KEYWORD, param.KEYWORD_ONLY]
            for param in sig.parameters.values()
            if param.name != "self"
        )
    except Exception:
        accepts_kwargs = False  # fallback: assume doesn't accept kwargs

    try:
        if accepts_kwargs:
            return ToolClass(**init_kwargs)
        else:
            return ToolClass()
    except Exception as e:
        expected_params_info = f"Expected constructor parameters for {ToolClass.__name__}: {sig}" if 'sig' in locals() else ""
        raise RuntimeError(
            f"Failed to instantiate tool '{actual_tool_string_id}'. "
            f"Provided config_params were: {init_kwargs}. "
            f"{expected_params_info} "
            f"Original tool init error: {e}"
        ) from e

def get_tool_instance_id(tool_id):
    config = PREDEFINED_TOOLS_CONFIG.get(tool_id)
    return config
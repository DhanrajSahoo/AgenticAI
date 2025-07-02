from crewai.tools import BaseTool
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel
import logging
from services.aws_services import CloudWatchLogHandler

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = CloudWatchLogHandler('agentic-ai', 'agentic-ai')
logger.addHandler(handler)

class StaticInputToolWrapper(BaseTool):
    def __init__(self, tool_instance: BaseTool, static_inputs: Dict[str, Any]):
        # 1) grab the original schema class
        schema_cls = getattr(tool_instance, "args_schema", None)
        if not (isinstance(schema_cls, type) and issubclass(schema_cls, BaseModel)):
            raise TypeError(f"Wrapped tool has invalid args_schema: {schema_cls!r}")

        # 2) initialize the BaseTool with the same schema class
        super().__init__(
            name=tool_instance.name,
            description=tool_instance.description,
            args_schema=schema_cls
        )

        # 3) keep references
        self._wrapped_tool  = tool_instance
        self._static_inputs = static_inputs

    def _run(self, *args: Any, **kwargs: Any) -> str:
        # Validate the static inputs exactly once here
        logger.info(f"[StaticInputToolWrapper] Using inputs: {self._static_inputs}")
        validated = self.args_schema(**self._static_inputs)
        # Delegate to the real tool
        return self._wrapped_tool.run(validated)

    def run(self, input_data: Optional[BaseModel] = None) -> str:
        # ignore any incoming input_data—always use your static_inputs
        return self._run()
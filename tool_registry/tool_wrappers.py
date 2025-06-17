from crewai.tools import BaseTool
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel


class StaticInputToolWrapper(BaseTool):
    def __init__(self, tool_instance: BaseTool, static_inputs: Dict[str, Any]):
        super().__init__(
            name=tool_instance.name,
            description=tool_instance.description
        )
        self._wrapped_tool = tool_instance
        self._static_inputs = static_inputs
        self.args_schema: Type[BaseModel] = tool_instance.args_schema

    def _run(self, *args, **kwargs) -> str:
        schema = self.args_schema(**self._static_inputs)
        return self._wrapped_tool.run(schema)

    def run(self, input_data: Optional[BaseModel] = None) -> str:
        return self._run()

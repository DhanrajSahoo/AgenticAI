from crewai.tools import BaseTool
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel


class StaticInputToolWrapper(BaseTool):
    def __init__(self, tool_instance: BaseTool, static_inputs: Dict[str, Any]):
        # Determine raw_schema
        raw_schema = tool_instance.args_schema

        # Distinguish between a Pydantic model class vs a function returning it
        if isinstance(raw_schema, type) and issubclass(raw_schema, BaseModel):
            schema_cls: Type[BaseModel] = raw_schema
        elif callable(raw_schema):
            schema_cls = raw_schema()
        else:
            raise TypeError(f"Cannot resolve args_schema from {raw_schema}")

        # Initialize BaseTool with correct schema
        super().__init__(
            name=tool_instance.name,
            description=tool_instance.description,
            args_schema=schema_cls
        )

        self._wrapped_tool = tool_instance
        self._static_inputs = static_inputs

    def _run(self, *args, **kwargs) -> str:
        schema_instance = self.args_schema(**self._static_inputs)
        return self._wrapped_tool.run(schema_instance)

    def run(self, input_data: Optional[BaseModel] = None) -> str:
        return self._run()
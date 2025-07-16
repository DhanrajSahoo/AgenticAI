import logging

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import os
from typing import Type
from crewai_tools import CSVSearchTool
from core.config import Config
os.environ["OPENAI_API_KEY"] = Config.openai_key
# os.environ["OPENAI_API_KEY"] = Config.openai_key

from services.aws_services import CloudWatchLogHandler

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = CloudWatchLogHandler('agentic-ai', 'agentic-ai')
logger.addHandler(handler)

class CsvQuerySchema(BaseModel):
    file_path: str = Field(..., description="Path to the Word file")
    prompt: str = Field(..., description="Question to ask the CSV")


class CsvQueryTool(BaseTool):
    name: str = "CSV Query Tool"
    description: str = "Runs a prompt against a CSV using RAG and returns the result"

    args_schema: Type[CsvQuerySchema] = CsvQuerySchema

    def _run(self, file_path: str, prompt: str) -> str:
        if "OPENAI_API_KEY" not in os.environ:
            raise RuntimeError("Please set OPENAI_API_KEY in env vars before using CSVQueryTool")
        logger.info("inside csv tool going to run tool")

        rag_tool = CSVSearchTool(
            csv=file_path,
            config={
                "llm": {
                    "provider": "openai",
                    "config": {
                        "model": "gpt-4o",
                        "temperature": 0.0,
                    },
                },
                "embedder": {
                    "provider": "openai",
                    "config": {
                        "model": "text-embedding-ada-002",
                    },
                },
            },
        )

        try:
            result = rag_tool._run(prompt)
            logger.info(f"result: {result}")
            return result
        except Exception as e:
            return f"Query failed: {e}"

    def run(self, input_data: CsvQuerySchema) -> str:
        return self._run(input_data.file_path, input_data.prompt)

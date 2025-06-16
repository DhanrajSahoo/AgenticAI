from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import os
from typing import Type
from crewai_tools import CSVSearchTool
from core.config import Config
os.environ["OPENAI_API_KEY"] = Config.openai_key
# os.environ["OPENAI_API_KEY"] = Config.openai_key


class CsvQuerySchema(BaseModel):
    csv_path: str = Field(..., description="Path to the Word file")
    query: str = Field(..., description="Question to ask the CSV")


class CsvQueryTool(BaseTool):
    name: str = "CSV Query Tool"
    description: str = "Runs a query against a CSV using RAG and returns the result"

    args_schema: Type[CsvQuerySchema] = CsvQuerySchema

    def _run(self, csv_path: str, query: str) -> str:
        if "OPENAI_API_KEY" not in os.environ:
            raise RuntimeError("Please set OPENAI_API_KEY in env vars before using CSVQueryTool")

        rag_tool = CSVSearchTool(
            csv=csv_path,
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
            return rag_tool._run(query)
        except Exception as e:
            return f"Query failed: {e}"

    def run(self, input_data: CsvQuerySchema) -> str:
        return self._run(input_data.csv_path, input_data.query)

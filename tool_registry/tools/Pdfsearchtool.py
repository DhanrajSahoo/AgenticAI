from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import os
from typing import Type
from crewai_tools import PDFSearchTool
os.environ["OPENAI_API_KEY"] = "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"


class PDFQuerySchema(BaseModel):
    pdf_path: str = Field(..., description="Path to the PDF file")
    query: str = Field(..., description="Question to ask the PDF")


class PDFQueryTool(BaseTool):
    name: str = "PDF Query Tool"
    description: str = "Runs a query against a PDF using RAG and returns the result"

    # <— annotate this field!
    args_schema: Type[PDFQuerySchema] = PDFQuerySchema

    def _run(self, pdf_path: str, query: str) -> str:
        if "OPENAI_API_KEY" not in os.environ:
            raise RuntimeError("Please set OPENAI_API_KEY in env vars before using PDFQueryTool")

        rag_tool = PDFSearchTool(
            pdf=pdf_path,
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

    def run(self, input_data: PDFQuerySchema) -> str:
        return self._run(input_data.pdf_path, input_data.query)

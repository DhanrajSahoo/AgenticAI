import logging
import pdb

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import os
from typing import Type
from crewai_tools import CSVSearchTool, RagTool
from core.config import Config
from db.vector_embeddings import Embeddings
from services.aws_services import CloudWatchLogHandler

embed = Embeddings()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = CloudWatchLogHandler('agentic-ai', 'agentic-ai')
logger.addHandler(handler)


class RAGQuerySchema(BaseModel):
    # I want to accept both "file_name" and "pdf_path" on input
    file_name: str = Field(
        ...,
        alias="pdf_path",
        description="Path to the file (alias: pdf_path)"
    )
    query: str = Field(..., description="Question to ask the file")

    model_config = {
        "populate_by_name": True,    # allow populating by the field name too
        "populate_by_alias": True,   # allow populating by alias
    }


class RAGQueryTool(BaseTool):
    name: str = "File Query Tool"
    description: str = "Runs a query against a File using RAG and returns the result"

    args_schema: Type[RAGQuerySchema] = RAGQuerySchema

    def _run(self, file_name: str, query: str) -> str:
        try:
            # file_name=file_name[5:]
            logger.info(f"Inside RAG tool filename:{file_name}, query:{query}")
            similar_text = embed.get_similar_text(file_name=file_name,prompt=query)
            # print(f"similar_text{similar_text}")
            try:
                return f"Query:-{query}\n\nContext:-{similar_text}"
            except Exception as e:
                logger.info(f"Query failed: {e}")
                return f"Query failed: {e}"
        except Exception as e:
            logger.info(f"error ragquery tool run{e}")

    def run(self, input_data: RAGQuerySchema) -> str:
        return self._run(input_data.file_name, input_data.query)

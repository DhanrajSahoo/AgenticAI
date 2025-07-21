import logging

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import os
from typing import Type
from crewai_tools import DOCXSearchTool
from core.config import Config
from db.vector_embeddings import Embeddings
embed = Embeddings()
os.environ["OPENAI_API_KEY"] = Config.openai_key
# os.environ["OPENAI_API_KEY"] = Config.openai_key

from services.aws_services import CloudWatchLogHandler

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = CloudWatchLogHandler('agentic-ai', 'agentic-ai')
logger.addHandler(handler)


class DocQuerySchema(BaseModel):
    file_path: str = Field(..., description="Path to the Word file")
    query: str = Field(..., description="Question to ask the DOC")


class DocQueryTool(BaseTool):
    name: str = "DOC Query Tool"
    description: str = "Runs a query against a DOC using RAG and returns the result"
    args_schema: Type[BaseModel] = DocQuerySchema  # ✅ This is correct now

    def _run(self, file_path: str, query: str) -> str:
        texts = embed._extract_docx_text(file_path)
        chunks = embed._chunk_text(texts)
        res = embed.provide_similar_txt_chroma(chunks, query, 'cosine')
        result = f"Query:-{query}\n\nContext:-{res}"
        return result

    def run(self, input_data: DocQuerySchema) -> str:
        return self._run(input_data.file_path, input_data.query)

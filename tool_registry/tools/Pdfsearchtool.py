import logging

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import os
from typing import Type
from crewai_tools import PDFSearchTool
from core.config import Config
from services.aws_services import CloudWatchLogHandler
from db.vector_embeddings import Embeddings

embed = Embeddings()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = CloudWatchLogHandler('agentic-ai', 'agentic-ai')
logger.addHandler(handler)

os.environ["OPENAI_API_KEY"] = Config.openai_key


class PDFQuerySchema(BaseModel):
    pdf_path: str = Field(..., description="Path to the PDF file")
    query: str = Field(..., description="Question to ask the PDF")


class PDFQueryTool(BaseTool):
    name: str = "PDF Query Tool"
    description: str = "Runs a query against a PDF using RAG and returns the result"

    args_schema: Type[BaseModel] = PDFQuerySchema  # ✅ This is correct now

    def _run(self, pdf_path: str, query: str) -> str:
        logger.info(f"query{query}, pdf_path:-{pdf_path}")
        texts = embed._extract_pdf_text(pdf_path)
        chunks = embed._chunk_text(texts)
        res = embed.provide_similar_txt_chroma(chunks, query, 'cosine')
        logger.info(f"res{res}")
        result = f"Query:-{query}\n\nContext:-{res}"
        logger.info(f"result:{result}")
        return result

    def run(self, input_data: PDFQuerySchema) -> str:
        return self._run(input_data.pdf_path, input_data.query)

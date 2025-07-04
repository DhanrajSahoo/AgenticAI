import logging
import tempfile
import requests
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


class FilereaderSchema(BaseModel):
    pdf_path: str = Field(..., description="Path to the PDF file")
    # query: str = Field(..., description="Question to ask the PDF")

# Helper function to ensure the file is available
def ensure_pdf_available(pdf_path: str) -> str:
    """Ensure the PDF file exists locally. If not, attempt to download it from the URL."""
    if os.path.exists(pdf_path):
        return pdf_path

    if pdf_path.startswith("http"):
        file_name = os.path.basename(pdf_path)
        tmp_path = os.path.join(tempfile.gettempdir(), file_name)

        try:
            response = requests.get(pdf_path, stream=True)
            response.raise_for_status()

            with open(tmp_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"Downloaded PDF to temp path: {tmp_path}")
            return tmp_path
        except Exception as e:
            logger.error(f"Failed to download PDF from URL: {pdf_path} | Error: {e}")
            raise FileNotFoundError(f"Could not download PDF from: {pdf_path}")
    
    raise FileNotFoundError(f"PDF not found locally or via URL: {pdf_path}")

class FILEReaderTool(BaseTool):
    name: str = "PDF Query Tool"
    description: str = "Runs a query against a PDF using RAG and returns the result"

    args_schema: Type[BaseModel] = FilereaderSchema  # ✅ This is correct now

    def _run(self, pdf_path: str) -> str:
        try:
            # Ensure the file is accessible
            pdf_path = ensure_pdf_available(pdf_path)
            # logger.info(f"Running query: {query} on PDF: {pdf_path}")

            # Extract, chunk and search
            texts = embed._extract_pdf_text(pdf_path)
            logger.info(f"Extracted text from PDF.")
            # chunks = embed._chunk_text(texts)
            # logger.info(f"Generated {len(chunks)} chunks from PDF.")
            # res = embed.provide_similar_txt_chroma(chunks, query, 'cosine')
            # logger.info(f"Semantic search result: {res}")

            result = texts
            return result
        except Exception as e:
            logger.error(f"Error in PDFQueryTool: {e}")
            return f"Error occurred while processing PDF: {e}"

    def run(self, input_data: FilereaderSchema) -> str:
        return self._run(input_data.pdf_path)

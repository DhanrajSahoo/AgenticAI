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


class PDFQuerySchema(BaseModel):
    file_path: str = Field(..., description="Path to the PDF file")
    prompt: str = Field(..., description="Question to ask the PDF")

# Helper function to ensure the file is available
def ensure_pdf_available(file_path: str) -> str:
    """Ensure the PDF file exists locally. If not, attempt to download it from the URL."""
    if os.path.exists(file_path):
        return file_path

    if file_path.startswith("http"):
        file_name = os.path.basename(file_path)
        tmp_path = os.path.join(tempfile.gettempdir(), file_name)

        try:
            response = requests.get(file_path, stream=True)
            response.raise_for_status()

            with open(tmp_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"Downloaded PDF to temp path: {tmp_path}")
            return tmp_path
        except Exception as e:
            logger.error(f"Failed to download PDF from URL: {file_path} | Error: {e}")
            raise FileNotFoundError(f"Could not download PDF from: {file_path}")
    
    raise FileNotFoundError(f"PDF not found locally or via URL: {file_path}")

class PDFQueryTool(BaseTool):
    name: str = "PDF Query Tool"
    description: str = "Runs a prompt against a PDF using RAG and returns the result"

    args_schema: Type[BaseModel] = PDFQuerySchema  # ✅ This is correct now

    def _run(self, file_path: str, prompt: str) -> str:
        try:
            # Ensure the file is accessible
            file_path = ensure_pdf_available(file_path)
            logger.info(f"Running prompt: {prompt} on PDF: {file_path}")

            # Extract, chunk and search
            texts = embed._extract_pdf_text(file_path)
            logger.info(f"Extracted text from PDF.")
            chunks = embed._chunk_text(texts)
            logger.info(f"Generated {len(chunks)} chunks from PDF.")
            res = embed.provide_similar_txt_chroma(chunks, prompt, 'cosine')
            logger.info(f"Semantic search result: {res}")

            result = f"Query:- {prompt}\n\nContext:- {res}"
            return result
        except Exception as e:
            logger.error(f"Error in PDFQueryTool: {e}")
            return f"Error occurred while processing PDF: {e}"

    def run(self, input_data: PDFQuerySchema) -> str:
        return self._run(input_data.file_path, input_data.prompt)

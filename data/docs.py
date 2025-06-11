import os
import logging
from io import BytesIO
from contextlib import contextmanager
from typing import List

import psycopg2
from pydantic import BaseModel, Field, SecretStr
#from sentence_transformers import SentenceTransformer
from PyPDF2 import PdfReader
from docx import Document


class DBConfig(BaseModel):
    """
    Database configuration settings.
    """
    name: str = Field(..., description="Database name")
    user: str = Field(..., description="Database user")
    password: SecretStr = Field(..., description="Database user password")
    host: str = Field("localhost", description="Database host")
    port: int = Field(5432, description="Database port number")


class EmbeddingsProcessor:
    """
    Processes documents (PDF, DOCX) to extract text, split into chunks,
    generate embeddings, and store them in a PostgreSQL database.
    """
    #, model_name: str
    def __init__(self,db_config,max_chunk_len: int = 1024):
        #self.model = SentenceTransformer(model_name)
        self.db_config = db_config
        self.max_chunk_len = max_chunk_len
        self.logger = logging.getLogger(self.__class__.__name__)
        logging.basicConfig(level=logging.INFO)

    @contextmanager
    def get_connection(self):
        """
        Context manager for PostgreSQL connection.
        """
        conn = psycopg2.connect(
            dbname=self.db_config.name,
            user=self.db_config.user,
            password=self.db_config.password.get_secret_value(),
            host=self.db_config.host,
            port=self.db_config.port,
        )
        try:
            yield conn
        finally:
            conn.close()

    def _ensure_vector_extension(self, conn: psycopg2.extensions.connection) -> None:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            conn.commit()
            self.logger.info("Ensured PostgreSQL 'vector' extension exists.")

    def _create_table(self, conn: psycopg2.extensions.connection, table_name: str) -> None:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id SERIAL PRIMARY KEY,
                    filename TEXT NOT NULL,
                    text TEXT NOT NULL,
                    embedding FLOAT8[] NOT NULL
                );
                """
            )
            conn.commit()
            self.logger.info(f"Table '%s' is ready.", table_name)

    def _drop_table(self, conn: psycopg2.extensions.connection, table_name: str) -> None:
        with conn.cursor() as cur:
            cur.execute(f"DROP TABLE IF EXISTS {table_name};")
            conn.commit()
            self.logger.info(f"Dropped table '%s' if existed.", table_name)

    def _chunk_text(self, text: str) -> List[str]:
        """
        Splits text into chunks not exceeding max_chunk_len.
        """
        words = text.split()
        chunks, current = [], []
        current_len = 0

        for word in words:
            if current_len + len(word) + 1 <= self.max_chunk_len:
                current.append(word)
                current_len += len(word) + 1
            else:
                chunks.append(" ".join(current))
                current = [word]
                current_len = len(word)

        if current:
            chunks.append(" ".join(current))

        return chunks

    def _extract_pdf_text(self, file_path) -> str:
        """
        Extracts all text from a PDF file.
        """
        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    def _extract_docx_text(self, file_path: str) -> str:
        """
        Extracts all text from a DOCX file.
        """
        doc = Document(file_path)
        return "\n".join(para.text for para in doc.paragraphs)

    # def _store_embeddings(
    #     self,
    #     conn: psycopg2.extensions.connection,
    #     table_name: str,
    #     filename: str,
    #     chunks: List[str],
    # ) -> None:
    #     """
    #     Generates embeddings for each chunk and stores them in the database.
    #     """
    #     with conn.cursor() as cur:
    #         for chunk in chunks:
    #             safe_text = chunk.replace("\x00", "")
    #             embedding = self.model.encode([safe_text])[0].tolist()
    #             cur.execute(
    #                 f"INSERT INTO {table_name} (filename, text, embedding) VALUES (%s, %s, %s);",
    #                 (filename, safe_text, embedding),
    #             )
    #         conn.commit()
    #         self.logger.info(
    #             "Inserted %d embeddings for '%s' into '%s'.",
    #             len(chunks), filename, table_name,
    #         )

    # def process_directory(self, folder_path: str, table_name: str) -> None:
    #     """
    #     Walks through a directory, processes PDF and DOCX files,
    #     and loads embeddings into the specified table.
    #     """
    #     with self.get_connection() as conn:
    #         self._ensure_vector_extension(conn)
    #         self._drop_table(conn, table_name)
    #         self._create_table(conn, table_name)
    #
    #         for root, _, files in os.walk(folder_path):
    #             for fname in files:
    #                 path = os.path.join(root, fname)
    #                 if fname.lower().endswith(".pdf"):
    #                     text = self._extract_pdf_text(path)
    #                 elif fname.lower().endswith(".docx"):
    #                     text = self._extract_docx_text(path)
    #                 else:
    #                     continue
    #
    #                 chunks = self._chunk_text(text)
    #                 self._store_embeddings(conn, table_name, os.path.basename(path), chunks)


# Example usage:
#
# from embeddings_processor import DBConfig, EmbeddingsProcessor
#
# db_cfg = DBConfig(
#     name="mydb",
#     user="postgres",
#     password=SecretStr("s3cr3t"),
# )
# proc = EmbeddingsProcessor("sentence-transformers/all-MiniLM-L6-v2", db_cfg)
# proc.process_directory("/path/to/docs", "documents_embeddings")

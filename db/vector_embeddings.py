import os
import shutil
import time
import faiss
from typing import List
from docx import Document
from pypdf import PdfReader
from chromadb.config import Settings
from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from core.config import Config
from .database import engine
from . import models as db_models

class Embeddings():
    def __init__(self,max_chunk_len: int = 500):
        self.max_chunk_len = max_chunk_len
        self.model = ''

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

    def _chunk_text(self,text):
        chunks = []
        current_chunk = ""

        # for word in text.split():
        #     if len(current_chunk) + len(word) + 1 <= self.max_chunk_len:
        #         current_chunk += " " + word
        #     else:
        #         chunks.append(current_chunk.strip())
        #         current_chunk = word
        # if current_chunk:
        #     chunks.append(current_chunk.strip())
        # return chunks
        if isinstance(text, list):
            text = " ".join(text)

        words = text.split()
        return [
            " ".join(words[i:i + self.max_chunk_len])
            for i in range(0, len(words), self.max_chunk_len)
        ]

    def provide_similar_txt(self,texts,prompt,search_tool):
        chunks = self._chunk_text(texts)
        if not chunks:
            return "No text chunks available for comparison."
        # Step 2: Load model and encode texts
        model = SentenceTransformer("all-MiniLM-L6-v2")
        if search_tool == 'cosine':
            text_embeddings = model.encode(chunks)

            # Step 3: Prompt to compare
            #prompt = "customer care number"
            prompt_embedding = model.encode([prompt])

            # Step 4: Cosine similarity
            similarities = cosine_similarity(prompt_embedding, text_embeddings)[0]

            # Step 5: Rank and get top N
            top_n = 10
            top_indices = similarities.argsort()[::-1][:top_n]

            # Step 6: Show results
            context = "\n"
            for idx in top_indices:
                #print(f"Score: {similarities[idx]:.4f}, Text: {chunks[idx]}")
                context += chunks[idx]
            return context

        elif search_tool == 'faiss':

            text_embeddings = model.encode(chunks).astype("float32")  # FAISS needs float32

            # Step 3: Build FAISS index
            dimension = text_embeddings.shape[1]
            index = faiss.IndexFlatL2(dimension)  # L2 = Euclidean; you can use IndexFlatIP for cosine-style
            index.add(text_embeddings)

            # Step 4: Encode prompt and search
            #prompt = "customer care number"
            prompt_embedding = model.encode([prompt]).astype("float32")
            k = 10  # top N
            distances, indices = index.search(prompt_embedding, k)

            context = "\n"
            # Step 5: Print top similar chunks
            for i, idx in enumerate(indices[0]):
                # print(f"Rank {i+1} | Distance: {distances[0][i]:.4f}")
                context +=chunks[idx]
            return context

    def provide_similar_txt_chroma(self, texts, prompt, search_tool):
        chunks = self._chunk_text(texts)
        if not chunks:
            return "No text chunks available for comparison."

        # Load model
        model = SentenceTransformer(
            "all-MiniLM-L6-v2",
            tokenizer_kwargs={"clean_up_tokenization_spaces": True}
        )

        if search_tool == "chroma":
            # Step 1: Set Chroma persist directory
            persist_dir = "./chroma_db"
            if os.path.exists(persist_dir):
                shutil.rmtree(persist_dir)  # Clean up old vectors
                time.sleep(2)

            client = PersistentClient(path=persist_dir, settings=Settings(anonymized_telemetry=False))
            collection = client.get_or_create_collection("doc_chunks")

            # Step 2: Embed text chunks
            embeddings = model.encode(chunks).tolist()

            # Step 3: Ingest into Chroma
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                collection.add(
                    documents=[chunk],
                    embeddings=[embedding],
                    ids=[f"chunk-{i}"]
                )

            # Step 4: Embed the prompt
            prompt_embedding = model.encode([prompt]).tolist()

            # Step 5: Search top K
            results = collection.query(
                query_embeddings=prompt_embedding,
                n_results=10
            )

            # Step 6: Combine results into context
            context = "\n".join(results["documents"][0])
            return context

        elif search_tool == "cosine":
            text_embeddings = model.encode(chunks)
            prompt_embedding = model.encode([prompt])
            similarities = cosine_similarity(prompt_embedding, text_embeddings)[0]
            top_indices = similarities.argsort()[::-1][:10]
            context = "\n".join([chunks[idx] for idx in top_indices])
            return context

        elif search_tool == "faiss":
            text_embeddings = model.encode(chunks).astype("float32")
            index = faiss.IndexFlatL2(text_embeddings.shape[1])
            index.add(text_embeddings)
            prompt_embedding = model.encode([prompt]).astype("float32")
            distances, indices = index.search(prompt_embedding, 10)
            context = "\n".join([chunks[idx] for idx in indices[0]])
            return context

        else:
            return "Invalid search_tool selected."

    # def create_embeddings(self,file_path,file_extension):
    #     if file_extension == '.pdf':
    #         file_text = self._extract_pdf_text(file_path)
    #     elif file_extension == '.docx':
    #         file_text = self._extract_docx_text(file_path)
    #     text_chunks = self._chunk_text(file_text)
    #     list_embeddings = []
    #     for text in text_chunks:
    #         cleaned_text = text.replace('\x00', '\ufffd')
    #         embeddings = self.model.encode([cleaned_text], convert_to_tensor=True)
    #         embedding = embeddings[0].tolist()
    #         list_embeddings.append(embedding)
    #     return list_embeddings

    def get_similar_chunks_via_orm(self,model, engine, filename: str, prompt: str, top_k: int = 3):
        # 1) embed the prompt
        emb = model.encode([prompt])[0].astype("float32").tolist()

        with Session(engine) as session:
            # 2) filter by filename and order by L2 distance
            results = (
                session
                .query(db_models.Document)
                .filter(db_models.Document.filename == filename)
                .order_by(db_models.Document.embedding.l2_distance(emb))
                .limit(top_k)
                .all()
            )

        return [doc.text for doc in results]

    def get_similar_text(self,file_name,prompt):
        similar_chunks = self.get_similar_chunks_via_orm(model=self.model, engine=engine,
                                                   filename=file_name,
                                                   prompt=prompt,
                                                   top_k=5
                                                   )
        most_similar_text = ""
        for i in similar_chunks:
            most_similar_text += i

        return most_similar_text
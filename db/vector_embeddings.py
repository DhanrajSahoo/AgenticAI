from typing import List
from docx import Document
from pypdf import PdfReader
import faiss

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from core.config import Config


class Embeddings():
    def __init__(self,max_chunk_len: int = 1024):
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
        for word in text.split():
            if len(current_chunk) + len(word) + 1 <= self.max_chunk_len:
                current_chunk += " " + word
            else:
                chunks.append(current_chunk.strip())
                current_chunk = word
        if current_chunk:
            chunks.append(current_chunk.strip())
        return chunks

    def provide_similar_txt(self,texts,prompt,search_tool):
        chunks = self._chunk_text(texts)
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
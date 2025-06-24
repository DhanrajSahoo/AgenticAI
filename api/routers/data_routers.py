import os
import logging
import tempfile
import requests
import chromadb
from io import BytesIO
from typing import List
from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends,File, UploadFile, Form
from crewai_tools import FileReadTool, CSVSearchTool, PDFSearchTool
from sentence_transformers import SentenceTransformer
from tool_registry.tools.AudioRecorder import VoiceRecorderTool
#from validators import file_validation


from db.models import Files, Document
from core.config import Config
from db.database import get_db_session
from db.vector_embeddings import Embeddings
from schemas import workflows_schema as schema
from schemas.tools_schema import FileCreate, FileQuery, FileDelete
from services.aws_services import upload_pdf_to_s3_direct
from db.crud import create_file_record, get_file_url_by_name, create_documents
from services.aws_services import CloudWatchLogHandler, delete_file_from_db_and_s3



logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = CloudWatchLogHandler('agentic-ai', 'agentic-ai')
logger.addHandler(handler)
embed  = Embeddings()

embedder = SentenceTransformer(
    "all-MiniLM-L6-v2",
    tokenizer_kwargs={"clean_up_tokenization_spaces": True}
)

async def save_upload_to_tempfile(
    upload: UploadFile,
    dir: str = None
) -> str:
    """
    Write an UploadFile to a NamedTemporaryFile and return its path.
    """
    # pick up the original extension
    ext = os.path.splitext(upload.filename)[1]
    # create a file that won’t auto-delete
    tmp = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=ext,
        dir=dir
    )
    # read & dump into it
    contents = await upload.read()
    tmp.write(contents)
    tmp.flush()
    tmp.close()

    # rewind source in case you need to re-read it elsewhere
    await upload.seek(0)
    return tmp.name


router = APIRouter(
    prefix="/data",
    tags=["Data"]
)
#'sentence-transformers/all-MiniLM-L6-v2',
#embed = EmbeddingsProcessor(db_config=Config)


@router.post("/upload/", status_code=201)
async def upload_file(files: List[UploadFile] = File(...),db: Session = Depends(get_db_session)):
    try:
        # validate_upload_files(files)
        all_chunks: List[str] = []
        file_name = ""
        url = ""
        file_path = ""
        for f in files:
            if f.filename[-4:].lower() == '.pdf':
                file_name += f.filename
                path = await save_upload_to_tempfile(f)
                file_path += path
                public_url = upload_pdf_to_s3_direct(
                    file=f,
                    bucket_name="apexon-agentic-ai",
                    s3_key=f.filename
                )
                url += public_url
                raw_text = embed._extract_pdf_text(path)
                chunk_texts = embed._chunk_text(raw_text)
                all_chunks.extend(chunk_texts)
                file = FileCreate(
                    file_name=f.filename,
                    file_url=public_url
                )
                create_file_record(db, file)
            elif f.filename[-4:] == '.wav':
                f.file.seek(0)
                file_name += f.filename
                path = await save_upload_to_tempfile(f)
                file_path += path

                public_url = upload_pdf_to_s3_direct(
                    file=f,
                    bucket_name="apexon-agentic-ai",
                    s3_key=f.filename
                )
                url += public_url

                file = FileCreate(
                    file_name=f.filename,
                    file_url=public_url
                )
                create_file_record(db, file)

                return {"Message": "Audio File uploaded successfully!"}
            elif f.filename[-4:] == '.mp3':
                f.file.seek(0)
                file_name += f.filename
                path = await save_upload_to_tempfile(f)
                file_path += path

                public_url = upload_pdf_to_s3_direct(
                    file=f,
                    bucket_name="apexon-agentic-ai",
                    s3_key=f.filename
                )
                url += public_url

                file = FileCreate(
                    file_name=f.filename,
                    file_url=public_url
                )
                create_file_record(db, file)

                return {"Message": "Audio File uploaded successfully!"}
            elif f.filename[-4:] == '.m4a':
                f.file.seek(0)
                file_name += f.filename
                path = await save_upload_to_tempfile(f)
                file_path += path

                public_url = upload_pdf_to_s3_direct(
                    file=f,
                    bucket_name="apexon-agentic-ai",
                    s3_key=f.filename
                )
                url += public_url

                file = FileCreate(
                    file_name=f.filename,
                    file_url=public_url
                )
                create_file_record(db, file)

                return {"Message": "Audio File uploaded successfully!"}
            elif f.filename[-4:] == '.csv':
                file_name += f.filename
                path = await save_upload_to_tempfile(f)
                file_path += path
                public_url = upload_pdf_to_s3_direct(
                    file=f,
                    bucket_name="apexon-agentic-ai",
                    s3_key=f.filename
                )

                url += public_url
                text = None
            elif f.filename[-5:] == '.docx':
                file_name += f.filename
                path = await save_upload_to_tempfile(f)
                file_path += path
                public_url = upload_pdf_to_s3_direct(
                    file=f,
                    bucket_name="apexon-agentic-ai",
                    s3_key=f.filename
                )

                url += public_url
                raw_text = embed._extract_docx_text(path)
                chunk_texts = embed._chunk_text(raw_text)
                all_chunks.extend(chunk_texts)

                file = FileCreate(
                    file_name=f.filename,
                    file_url=public_url
                )
                create_file_record(db, file)
                return {"Message": "Word File uploaded successfully!"}
            elif f.filename[-5:].lower() == '.json':
                file_name += f.filename
                path = await save_upload_to_tempfile(f)
                file_path += path
                public_url = upload_pdf_to_s3_direct(
                    file=f, bucket_name="apexon-agentic-ai", s3_key=f.filename
                )
                url += public_url
                raw_text = embed._extract_json_text(path)
                chunk_texts = embed._chunk_text(raw_text)
                all_chunks.extend(chunk_texts)
                file = FileCreate(file_name=f.filename, file_url=public_url)
                create_file_record(db, file)

            elif f.filename[-3:].lower() == '.py':
                file_name += f.filename
                path = await save_upload_to_tempfile(f)
                file_path += path
                public_url = upload_pdf_to_s3_direct(
                    file=f, bucket_name="apexon-agentic-ai", s3_key=f.filename
                )
                url += public_url
                raw_text = embed._extract_python_text(path)
                chunk_texts = embed._chunk_text(raw_text)
                all_chunks.extend(chunk_texts)
                file = FileCreate(file_name=f.filename, file_url=public_url)
                create_file_record(db, file)

            elif f.filename[-5:].lower() == '.html':
                file_name += f.filename
                path = await save_upload_to_tempfile(f)
                file_path += path
                public_url = upload_pdf_to_s3_direct(
                    file=f, bucket_name="apexon-agentic-ai", s3_key=f.filename
                )
                url += public_url
                raw_text = embed._extract_html_text(path)
                chunk_texts = embed._chunk_text(raw_text)
                all_chunks.extend(chunk_texts)
                file = FileCreate(file_name=f.filename, file_url=public_url)
                create_file_record(db, file)

            elif f.filename[-5:].lower() == '.yaml' or f.filename[-4:].lower() == '.yml':
                file_name += f.filename
                path = await save_upload_to_tempfile(f)
                file_path += path
                public_url = upload_pdf_to_s3_direct(
                    file=f, bucket_name="apexon-agentic-ai", s3_key=f.filename
                )
                url += public_url
                raw_text = embed._extract_yaml_text(path)
                chunk_texts = embed._chunk_text(raw_text)
                all_chunks.extend(chunk_texts)
                file = FileCreate(file_name=f.filename, file_url=public_url)
                create_file_record(db, file)

            else:
                text = None

        created = create_documents(
            db,
            filename=file_name,
            file_path=file_path,
            embedder=embedder,
            url=url,
            texts=all_chunks
        )

        return {"Message": "File Uploaded and vector created Successfully"}
    except Exception as e:
        #print(f"while uploading file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to upload a file: {str(e)}")

@router.post("/get_files/", status_code=201)
def fetch_file_url(payload: FileQuery, db: Session = Depends(get_db_session)):
    try:
        # If file_name is not provided, return all file names
        if not payload.file_name:
            file_names = db.query(Files.file_name).all()
            return {"file_names": [f[0] for f in file_names]}  # unpack tuples

        # Else, proceed with download logic
        s3_url = get_file_url_by_name(db, payload.file_name)
        response = requests.get(s3_url, stream=True)
        response.raise_for_status()

        # Extract original filename
        file_name = s3_url.split("/")[-1]

        # Create a temporary file path
        tmp_dir = tempfile.gettempdir()
        tmp_file_path = os.path.join(tmp_dir, file_name)

        # Write the content to the temp file
        with open(tmp_file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        if not s3_url:
            raise HTTPException(status_code=404, detail="File not found")
        #logger.info({"file_name": payload.file_name, "file_url": tmp_file_path})
        return {"file_name": payload.file_name, "file_url": tmp_file_path}
    except Exception as e:
        logger.info(f"error{e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch the url: {str(e)}")

@router.delete("/delete-file/")
def delete_file(payload: FileDelete, db: Session = Depends(get_db_session)):
    bucket_name = "apexon-agentic-ai"

    success = delete_file_from_db_and_s3(db, payload.file_name, bucket_name)

    if not success:
        raise HTTPException(status_code=404, detail="File not found")

    return {"message": f"File '{payload.file_name}' deleted from DB and S3."}

@router.post("/similar-text/")
async def get_similar_text(prompt: str = Form(...),
    vector_search_engine: str = Form(...),files: List[UploadFile] = File(...)):
    try:
        logger.info(f"get similar text")
        content = "\n"
        for f in files:
            path =await save_upload_to_tempfile(f)
            if f.filename[-4:] == '.pdf':
                raw_text = embed._extract_pdf_text(path)
                content+=raw_text

            elif f.filename[-5:] == '.docx':
                raw_text = embed._extract_docx_text(path)
                content += raw_text

        similar_text = embed.provide_similar_txt(texts=content,prompt=prompt,search_tool=vector_search_engine)

        return {"SimilarText": f"{similar_text}"}
    except Exception as e:
        logger.info(f"Failed to get the similar text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get the similar text: {str(e)}")

@router.get("/clear-chroma/")
def clear_chroma():
    try:
        client = chromadb.Client()
        client.reset()
        logger.info({"Message": f"Reset Chroma db successfully"})
        return {"Message": f"Reset Chroma db successfully"}
    except Exception as e:
        logger.info(f"{e}e")
        raise HTTPException(status_code=500, detail=f"Failed to clear chroma: {str(e)}")

@router.get("/filenames/", response_model=List[str])
def list_filenames(db: Session = Depends(get_db_session)):
    """
    Returns a list of all distinct filenames stored in vector_db.
    """
    try:
        # Query for distinct filename values
        rows = (
            db
            .query(Document.filename)
            .distinct()
            .all()
        )
        # rows is a list of 1-tuples like [("file1.csv",), ("report.pdf",), ...]
        return [filename for (filename,) in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unable to fetch filenames: {e}")



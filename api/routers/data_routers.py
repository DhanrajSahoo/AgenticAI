import os
import logging
import tempfile
import requests
from io import BytesIO
from typing import List
from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends,File, UploadFile
from crewai_tools import FileReadTool, CSVSearchTool, PDFSearchTool
#from validators import file_validation

from db.models import Files
from core.config import Config
from db.database import get_db_session
from data.docs import EmbeddingsProcessor
from schemas import workflows_schema as schema
from schemas.tools_schema import FileCreate, FileQuery, FileDelete
from services.aws_services import upload_pdf_to_s3_direct
from db.crud import create_file_record, get_file_url_by_name
from services.aws_services import CloudWatchLogHandler, delete_file_from_db_and_s3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = CloudWatchLogHandler('agentic-ai', 'agentic-ai')
logger.addHandler(handler)

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
embed = EmbeddingsProcessor(db_config=Config)


@router.post("/upload/", status_code=201)
async def upload_file(files: List[UploadFile] = File(...),db: Session = Depends(get_db_session)):
    try:
        # validate_upload_files(files)
        text = ""
        for f in files:
            if f.filename[-4:].lower() == '.pdf':
                logger.info(f"inside pdf {f.filename}")
                public_url = upload_pdf_to_s3_direct(
                    file=f,
                    bucket_name="apexon-agentic-ai",
                    s3_key=f.filename
                )
                logger.info(f"public url:{public_url}")
                file = FileCreate(
                    file_name=f.filename,
                    file_url=public_url
                )
                create_file_record(db, file)
                logger.info(f"create file done")
                #logger.info({"Message": "PDF File uploaded successfully!"})
                return {"Message": "PDF File uploaded successfully!"}
            elif f.filename[-4:] == '.wav':
                public_url = upload_pdf_to_s3_direct(
                    file=f,
                    bucket_name="apexon-agentic-ai",
                    s3_key=f.filename
                )
                file = FileCreate(
                    file_name=f.filename,
                    file_url=public_url
                )
                create_file_record(db, file)
                return {"Message": "Audio File uploaded successfully!"}
            elif f.filename[-4:] == '.csv':
                public_url = upload_pdf_to_s3_direct(
                    file=f,
                    bucket_name="apexon-agentic-ai",
                    s3_key=f.filename
                )
                file = FileCreate(
                    file_name=f.filename,
                    file_url=public_url
                )
                create_file_record(db, file)
                return {"Message": "CSV File uploaded successfully!"}
                # text+=path
                # file_reader = FileReadTool(file_path=path)
            elif f.filename[-5:] == '.docx':
                public_url = upload_pdf_to_s3_direct(
                    file=f,
                    bucket_name="apexon-agentic-ai",
                    s3_key=f.filename
                )
                file = FileCreate(
                    file_name=f.filename,
                    file_url=public_url
                )
                create_file_record(db, file)
                return {"Message": "Word File uploaded successfully!"}
        #logger.info({"Message": text})
        return {"Message": text}
    except Exception as e:
        logger.info(f"while uploading file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to upload a file: {str(e)}")


@router.get("/get_files/", status_code=201)
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

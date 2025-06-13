import os
import tempfile
from io import BytesIO
from typing import List
from fastapi import APIRouter, HTTPException, Depends,File, UploadFile
from crewai_tools import FileReadTool, CSVSearchTool, PDFSearchTool
#from validators import file_validation
from data.docs import EmbeddingsProcessor
from core.config import Config
from schemas import workflows_schema as schema

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
async def upload_file(files: List[UploadFile] = File(...)):
    try:
        # validate_upload_files(files)
        text = ""
        for f in files:
            if f.filename[-4:] == '.pdf':
                contents = await f.read()
                path = await save_upload_to_tempfile(f)
                text += path
                #file_reader = PDFSearchTool(file_path=path)
                # data = embed._extract_pdf_text(file_path=BytesIO(contents))
                # text += data
                # … your storage logic …
                # saved.append(f.filename)
            elif f.filename[-4:] == '.wav':
                path = await save_upload_to_tempfile(f)
                text += path
            elif f.filename[-5:] == '.docx':
                path = await save_upload_to_tempfile(f)
            elif f.filename[-4:] == '.csv':
                path = await save_upload_to_tempfile(f)
                text += path
                #file_reader = FileReadTool(file_path=path)

        return {"Message": text}
    except Exception as e:
        print(f"while uploading file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to upload a file: {str(e)}")
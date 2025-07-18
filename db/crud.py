import os
import uuid

import pandas as pd
from sqlalchemy.orm import Session
from typing import List, Optional

from . import models as db_models
from schemas import workflows_schema
from schemas.tools_schema import FileCreate


def create_workflow(db: Session, workflow_payload_data: workflows_schema.WorkflowDataContent) -> db_models.DBWorkflow:
    # workflow_create_data contains workflow_name and nodes
    db_workflow = db_models.DBWorkflow(
        name=workflow_payload_data.workflow_name,
        description=workflow_payload_data.workflow_description,
        workflow_data={"nodes": [node.model_dump() for node in workflow_payload_data.nodes]},
        is_deleted=False
    )
    db.add(db_workflow)
    db.commit()
    db.refresh(db_workflow)
    return db_workflow


def get_workflow(db: Session, workflow_id: uuid.UUID) -> Optional[db_models.DBWorkflow]:
    return db.query(db_models.DBWorkflow).filter(
        db_models.DBWorkflow.id == workflow_id,
        db_models.DBWorkflow.is_deleted == False
    ).first()


def get_workflows(db: Session, skip: int = 0, limit: int = 100) -> List[db_models.DBWorkflow]:
    return db.query(db_models.DBWorkflow).filter(
        db_models.DBWorkflow.is_deleted == False
    ).order_by(db_models.DBWorkflow.created_at.desc()).offset(skip).limit(limit).all()


def update_workflow(
        db: Session, workflow_id: uuid.UUID, workflow_update_data: workflows_schema.WorkflowDataContent
) -> Optional[db_models.DBWorkflow]:
    db_workflow = get_workflow(db, workflow_id)
    if db_workflow:
        if workflow_update_data.workflow_name:
            db_workflow.name = workflow_update_data.workflow_name
            db_workflow.description = workflow_update_data.workflow_description

        if workflow_update_data.nodes is not None:
            db_workflow.workflow_data = {
                **(db_workflow.workflow_data or {}),
                "nodes": [node.model_dump() for node in workflow_update_data.nodes]
            }
        else:
            db_workflow.workflow_data = {
                **(db_workflow.workflow_data or {}),
                "nodes": []
            }

        db.commit()
        db.refresh(db_workflow)

    return db_workflow


def soft_delete_workflow(db: Session, workflow_id: uuid.UUID) -> bool:
    db_workflow = db.query(db_models.DBWorkflow).filter(
        db_models.DBWorkflow.id == workflow_id
    ).first()

    if db_workflow and not db_workflow.is_deleted:
        db_workflow.is_deleted = True
        db.commit()
        return True
    return False

def create_file_record(db: Session, file_data: FileCreate) -> db_models.Files:
    db_file = db_models.Files(
        file_name=file_data.file_name,
        file_url=file_data.file_url
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

def get_file_url_by_name(db: Session, file_name: str) -> str:
    file_record = db.query(db_models.Files).filter(db_models.Files.file_name == file_name).first()
    if file_record:
        return file_record.file_url
    return None  # or raise HTTPException if not found

def create_documents(
    db: Session,
    *,
    filename: str,
    file_path: str,
    embedder,
    url: str,
    texts: Optional[List[str]] = None
) -> List[db_models.Document]:
    """
    Inserts each text chunk or (for CSV/Excel) each row-as-text
    with its embedding as a Document row in the DB.

    - filename: original upload filename (used for grouping/filtering)
    - file_path: path on disk to the saved upload
    - embedder: a SentenceTransformer (or similar) with .encode(...)
    - url: the public URL you stored in S3
    - texts: ONLY used for non-tabular files (PDF/DOCX chunks)
    """
    docs: List[db_models.Document] = []
    ext = os.path.splitext(filename)[1].lower()

    # 1) Build the single text blob
    if ext in {".csv", ".xls", ".xlsx"}:
        # load into DataFrame
        if ext == ".csv":
            df = pd.read_csv(file_path)
        else:
            sheets = pd.read_excel(file_path, sheet_name=None)
            df = pd.concat(sheets.values(), ignore_index=True)
        # turn the entire table into one string
        # you can customize sep or exclude index if you want
        full_text = df.to_csv(index=False)
    else:
        # for PDF/DOCX: join all your pre-chunked texts
        full_text = "\n".join(texts or [])

    # 2) clean NULLs
    cleaned = full_text.replace("\x00", "\ufffd")

    # 3) embed once
    tensor = embedder.encode([cleaned], convert_to_tensor=True)
    vector = tensor[0].tolist()

    # 4) single ORM object
    doc = db_models.Document(
        filename=filename,
        text=cleaned,
        embedding=vector,
        url=url
    )
    docs.append(doc)

    # 5) save & refresh
    db.add_all(docs)
    db.commit()
    for d in docs:
        db.refresh(d)

    return docs
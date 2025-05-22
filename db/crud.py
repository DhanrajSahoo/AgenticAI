from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid

from . import models as db_models
from schemas import workflows_schema


def create_workflow(db: Session, workflow_create_data: workflows_schema.WorkflowCreate) -> db_models.DBWorkflow:
    db_workflow = db_models.DBWorkflow(
        name=workflow_create_data.name,
        workflow_data=workflow_create_data.model_dump()
    )
    db.add(db_workflow)
    db.commit()
    db.refresh(db_workflow)
    return db_workflow


def get_workflow(db: Session, workflow_id: uuid.UUID) -> Optional[db_models.DBWorkflow]:
    return db.query(db_models.DBWorkflow).filter(db_models.DBWorkflow.id == workflow_id).first()


def get_workflows(db: Session, skip: int = 0, limit: int = 100) -> List[db_models.DBWorkflow]:
    return db.query(db_models.DBWorkflow).order_by(db_models.DBWorkflow.created_at.desc()).offset(skip).limit(
        limit).all()


def update_workflow(
        db: Session, workflow_id: uuid.UUID, workflow_update_data: workflows_schema.WorkflowUpdate
) -> Optional[db_models.DBWorkflow]:
    db_workflow = get_workflow(db, workflow_id)
    if db_workflow:
        current_workflow_content = workflows_schema.WorkflowBase(**db_workflow.workflow_data)

        update_dict = workflow_update_data.model_dump(exclude_unset=True)

        updated_content_data = current_workflow_content.model_copy(update=update_dict)

        db_workflow.name = updated_content_data.name
        db_workflow.workflow_data = updated_content_data.model_dump()

        db.commit()
        db.refresh(db_workflow)
    return db_workflow


def delete_workflow(db: Session, workflow_id: uuid.UUID) -> bool:
    db_workflow = get_workflow(db, workflow_id)
    if db_workflow:
        db.delete(db_workflow)
        db.commit()
        return True
    return False
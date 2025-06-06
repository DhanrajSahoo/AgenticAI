from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from . import models as db_models
from schemas import workflows_schema


def create_workflow(db: Session, workflow_payload_data: workflows_schema.WorkflowDataContent) -> db_models.DBWorkflow:
    # workflow_create_data contains workflow_name and nodes
    db_workflow = db_models.DBWorkflow(
        name=workflow_payload_data.workflow_name,
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
        db: Session, workflow_id: uuid.UUID, workflow_update_data: workflows_schema.WorkflowUpdatePayload
) -> Optional[db_models.DBWorkflow]:
    db_workflow = get_workflow(db, workflow_id)
    if db_workflow:
        update_dict = workflow_update_data.model_dump(exclude_unset=True)

        if "workflow_name" in update_dict:
            db_workflow.name = update_dict["workflow_name"]

        if "nodes" in update_dict and update_dict["nodes"] is not None:
            current_db_data = db_workflow.workflow_data if isinstance(db_workflow.workflow_data, dict) else {}
            current_db_data["nodes"] = [node.model_dump() for node in workflow_update_data.nodes]
            db_workflow.workflow_data = current_db_data
        elif "nodes" in update_dict and update_dict["nodes"] is None:
            current_db_data = db_workflow.workflow_data if isinstance(db_workflow.workflow_data, dict) else {}
            current_db_data["nodes"] = []
            db_workflow.workflow_data = current_db_data

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
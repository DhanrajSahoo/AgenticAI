from sqlalchemy.orm import Session
from typing import List, Optional, Any
import uuid

from db import crud
from schemas import workflows_schema as schema
from .crew_builder import CrewBuilder


def create_workflow(db: Session, workflow_data: schema.WorkflowCreate) -> schema.WorkflowInDB:
    db_workflow_obj = crud.create_workflow(db=db, workflow_create_data=workflow_data)
    return schema.WorkflowInDB(
        id=db_workflow_obj.id,
        name=db_workflow_obj.name,
        nodes=db_workflow_obj.workflow_data.get("nodes", []),
        edges=db_workflow_obj.workflow_data.get("edges", []),
        created_at=db_workflow_obj.created_at,
        updated_at=db_workflow_obj.updated_at
    )


def get_workflow(db: Session, workflow_id: uuid.UUID) -> Optional[schema.WorkflowInDB]:
    db_workflow_obj = crud.get_workflow(db=db, workflow_id=workflow_id)
    if db_workflow_obj:
        return schema.WorkflowInDB(
            id=db_workflow_obj.id,
            name=db_workflow_obj.name,
            nodes=db_workflow_obj.workflow_data.get("nodes", []),
            edges=db_workflow_obj.workflow_data.get("edges", []),
            created_at=db_workflow_obj.created_at,
            updated_at=db_workflow_obj.updated_at
        )
    return None


def list_workflows(db: Session, skip: int = 0, limit: int = 100) -> List[schema.WorkflowInDB]:
    db_workflows_list = crud.get_workflows(db=db, skip=skip, limit=limit)
    return [
        schema.WorkflowInDB(
            id=wf.id,
            name=wf.name,
            nodes=wf.workflow_data.get("nodes", []),
            edges=wf.workflow_data.get("edges", []),
            created_at=wf.created_at,
            updated_at=wf.updated_at
        ) for wf in db_workflows_list
    ]


def update_workflow(
        db: Session, workflow_id: uuid.UUID, workflow_update_data: schema.WorkflowUpdate
) -> Optional[schema.WorkflowInDB]:
    updated_db_workflow = crud.update_workflow(
        db=db, workflow_id=workflow_id, workflow_update_data=workflow_update_data
    )
    if updated_db_workflow:
        return schema.WorkflowInDB(
            id=updated_db_workflow.id,
            name=updated_db_workflow.name,
            nodes=updated_db_workflow.workflow_data.get("nodes", []),
            edges=updated_db_workflow.workflow_data.get("edges", []),
            created_at=updated_db_workflow.created_at,
            updated_at=updated_db_workflow.updated_at
        )
    return None


def delete_workflow(db: Session, workflow_id: uuid.UUID) -> bool:
    return crud.delete_workflow(db=db, workflow_id=workflow_id)


def run_workflow(db: Session, workflow_id: uuid.UUID) -> schema.WorkflowExecutionResult:
    workflow_in_db = get_workflow(db, workflow_id)
    if not workflow_in_db:
        raise ValueError("Workflow not found for execution.")

    builder = CrewBuilder(workflow_in_db)
    output = builder.build_and_run()

    return schema.WorkflowExecutionResult(
        workflow_id=workflow_id,
        status="success",
        output=str(output)
    )
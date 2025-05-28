from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict
import uuid
import logging

from schemas import workflows_schema as schema
from services import workflow_service
from services.crew_builder import CrewBuilderError
from db.database import get_db_session

router = APIRouter(
    prefix="/workflows",
    tags=["Workflows"]
)
logger = logging.getLogger(__name__)


@router.post("/", response_model=schema.WorkflowResponse, status_code=201)
async def api_create_workflow(
        workflow_data: schema.WorkflowCreatePayload,
        db: Session = Depends(get_db_session)
):
    try:
        return workflow_service.create_workflow(db=db, workflow_data=workflow_data)
    except Exception as e:
        logger.error(f"Error creating workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")


@router.get("/", response_model=List[schema.WorkflowResponse])
async def api_list_workflows(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db_session)
):
    try:
        return workflow_service.list_workflows(db=db, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error listing workflows: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list workflows.")


@router.get("/{workflow_id}", response_model=schema.WorkflowResponse)
async def api_get_workflow(
        workflow_id: uuid.UUID,
        db: Session = Depends(get_db_session)
):
    db_workflow = workflow_service.get_workflow(db=db, workflow_id=workflow_id)
    if db_workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return db_workflow


@router.post("/{workflow_id}/update", response_model=schema.WorkflowResponse)
async def api_update_workflow(
    workflow_id: uuid.UUID,
    workflow_data: schema.WorkflowUpdatePayload,
    db: Session = Depends(get_db_session)
):
    try:
        updated_workflow = workflow_service.update_workflow(
            db=db, workflow_id=workflow_id, workflow_update_data=workflow_data
        )
        if updated_workflow is None:
            raise HTTPException(status_code=404, detail="Workflow not found or already deleted")
        return updated_workflow
    except Exception as e:
        logger.error(f"Error updating workflow {workflow_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update workflow: {str(e)}")


@router.post("/{workflow_id}/delete", status_code=200, response_model=Dict[str, str])
async def api_delete_workflow(
    workflow_id: uuid.UUID,
    db: Session = Depends(get_db_session)
):
    if not workflow_service.delete_workflow(db=db, workflow_id=workflow_id):
        raise HTTPException(status_code=404, detail="Workflow not found or already deleted")
    return {"message": "Workflow marked as deleted successfully"}


@router.post("/{workflow_id}/run", response_model=schema.WorkflowExecutionResult)
async def api_run_workflow(
        workflow_id: uuid.UUID,
        db: Session = Depends(get_db_session)
):
    logger.info(f"Attempting to run workflow ID: {workflow_id}")
    existing_workflow = workflow_service.get_workflow(db=db, workflow_id=workflow_id)
    if not existing_workflow:
        logger.warning(f"Workflow ID: {workflow_id} not found for execution.")
        raise HTTPException(status_code=404, detail="Workflow not found")

    try:
        logger.info(f"Running workflow: {existing_workflow.workflow_name}")
        return workflow_service.run_workflow_service(db=db, workflow_id=workflow_id)
    except CrewBuilderError as e:  # Catch specific builder errors
        logger.error(f"CrewBuilder error for workflow {workflow_id}: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Workflow configuration error: {str(e)}")
    except EnvironmentError as e:
        logger.error(f"Environment error running workflow {workflow_id}: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        logger.error(f"Validation or structural error running workflow {workflow_id}: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Workflow processing error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error running workflow {workflow_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")
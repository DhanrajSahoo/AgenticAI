import logging

from sqlalchemy.orm import Session
from typing import List, Optional, Any
import uuid

from db import crud
from schemas import workflows_schema as schema
from .crew_builder import CrewBuilder, CrewBuilderError
from services.aws_services import CloudWatchLogHandler

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = CloudWatchLogHandler('agentic-ai', 'agentic-ai')
logger.addHandler(handler)


def create_workflow(db: Session, workflow_data_content: schema.WorkflowDataContent) -> schema.WorkflowResponse:
    db_workflow_obj = crud.create_workflow(db=db, workflow_payload_data=workflow_data_content)

    ui_nodes_from_db = []
    if db_workflow_obj.workflow_data and "nodes" in db_workflow_obj.workflow_data:
        for node_dict in db_workflow_obj.workflow_data["nodes"]:
            ui_nodes_from_db.append(schema.UINode(**node_dict))

    return schema.WorkflowResponse(
        id=db_workflow_obj.id,
        workflow_name=db_workflow_obj.name,
        workflow_description=db_workflow_obj.description,
        nodes=ui_nodes_from_db,
        created_at=db_workflow_obj.created_at,
        updated_at=db_workflow_obj.updated_at
    )


def get_workflow(db: Session, workflow_id: uuid.UUID) -> Optional[schema.WorkflowResponse]:
    db_workflow_obj = crud.get_workflow(db=db, workflow_id=workflow_id)
    if db_workflow_obj:
        ui_nodes_from_db = []
        if db_workflow_obj.workflow_data and "nodes" in db_workflow_obj.workflow_data:
            for node_dict in db_workflow_obj.workflow_data["nodes"]:
                ui_nodes_from_db.append(schema.UINode(**node_dict))

        return schema.WorkflowResponse(
            id=db_workflow_obj.id,
            workflow_name=db_workflow_obj.name,
            workflow_description=db_workflow_obj.description or "",
            nodes=ui_nodes_from_db,
            created_at=db_workflow_obj.created_at,
            updated_at=db_workflow_obj.updated_at
        )
    return None


def list_workflows(db: Session, payload: schema.WorkflowListPayload) -> List[schema.WorkflowResponse]:
    db_workflows_list = crud.get_workflows(db=db, skip=payload.skip, limit=payload.limit)
    response_list = []
    for wf in db_workflows_list:
        ui_nodes_from_db = []
        if wf.workflow_data and "nodes" in wf.workflow_data:
            for node_dict in wf.workflow_data["nodes"]:
                ui_nodes_from_db.append(schema.UINode(**node_dict))
        response_list.append(
            schema.WorkflowResponse(
                id=wf.id,
                workflow_name=wf.name,
                workflow_description=wf.description or "",
                nodes=ui_nodes_from_db,
                created_at=wf.created_at,
                updated_at=wf.updated_at
            )
        )
    return response_list


def update_workflow(
        db: Session, workflow_id: uuid.UUID, workflow_update_data: schema.WorkflowUpdatePayload
) -> Optional[schema.WorkflowResponse]:
    updated_db_workflow = crud.update_workflow(
        db=db, workflow_id=workflow_id, workflow_update_data=workflow_update_data
    )
    if updated_db_workflow:
        ui_nodes_from_db = []
        if updated_db_workflow.workflow_data and "nodes" in updated_db_workflow.workflow_data:
            for node_dict in updated_db_workflow.workflow_data["nodes"]:
                ui_nodes_from_db.append(schema.UINode(**node_dict))

        return schema.WorkflowResponse(
            id=updated_db_workflow.id,
            workflow_name=updated_db_workflow.name,
            workflow_description=updated_db_workflow.description,
            nodes=ui_nodes_from_db,
            created_at=updated_db_workflow.created_at,
            updated_at=updated_db_workflow.updated_at
        )
    return None


def delete_workflow(db: Session, workflow_id: uuid.UUID) -> bool:
    return crud.soft_delete_workflow(db=db, workflow_id=workflow_id)


def run_workflow_service(payload,db: Session, workflow_id: uuid.UUID) -> schema.WorkflowExecutionResult:
    workflow_response_data = get_workflow(db, workflow_id)
    if not workflow_response_data:
        # This case should be caught by the router, but defensive check
        raise ValueError(f"Workflow with ID {workflow_id} not found for execution.")

    if payload.file_path:
        for node in workflow_response_data.nodes:
            if "tool_input" not in node.data and "tool_name" in node.data:
                # Inject or overwrite the tool_inputs
                node.data['tool_inputs'] = {
                    "pdf_path": payload.file_path,
                    "query": payload.prompt
                }
        if payload.prompt:
            for node in workflow_response_data.nodes:
                if 'tool_name' in node.data and node.data['tool_name'] == 'PdfSearchTool':
                    # Check if tool_inputs exists, else initialize it
                    if 'tool_inputs' not in node.data:
                        node.data['tool_inputs'] = {}

                    # Update the values as you want
                    # node.data['tool_inputs']['pdf_path'] = '/your/new/path.pdf'
                    node.data['tool_inputs']['query'] = payload.prompt

        # CrewBuilder expects a list of UINodes
    builder = CrewBuilder(workflow_response_data.nodes)
    logger.info(f"builder:{builder}")
    logger.info(f"nodes:{workflow_response_data.nodes}")
    output = builder.build_and_run()

    return schema.WorkflowExecutionResult(
        workflow_id=workflow_id,
        status="success",
        output=str(output)
    )
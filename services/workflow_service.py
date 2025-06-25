import logging
import os
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


def run_workflow_service(payload, db: Session, workflow_id: uuid.UUID) -> schema.WorkflowExecutionResult:
    try:
        workflow = get_workflow(db, workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        # 1) Auto-populate `source` from `parents`
        for node in workflow.nodes:
            if (node.id.startswith("agent-") or node.id.startswith("task-")) and not node.source:
                node.source = list(node.parents)

        # 2) Inject tool_inputs for CSV / PDF / RAG
        for node in workflow.nodes:
            name = node.data.get("tool_name")
            if not name:
                continue

            node.data.setdefault("tool_inputs", {})

            # always inject the user prompt if present
            if payload.prompt:
                node.data["tool_inputs"]["query"] = payload.prompt

            # CSV
            if name in ("CsvSearchTool", "CSV Query Tool") and payload.file_path:
                node.data["tool_inputs"]["csv_path"] = payload.file_path

            # PDF Query Tool
            elif name == "PdfSearchTool" and payload.file_path:
                node.data["tool_inputs"]["pdf_path"] = payload.file_path

            # RAG Tool
            elif name in ("RagTool", "File Query Tool"):
                # prefer explicit file_name, else fallback to basename of file_path
                if getattr(payload, "file_name", None):
                    node.data["tool_inputs"]["file_name"] = payload.file_name
                elif payload.file_path:
                    node.data["tool_inputs"]["file_name"] = os.path.basename(payload.file_path)

        # hand off to your builder
        builder = CrewBuilder(workflow.nodes)
        result = builder.build_and_run()
        return schema.WorkflowExecutionResult(
            workflow_id=workflow_id, status="success", output=str(result)
        )
    except Exception as e:
        logger.info(f"error at running workflow:{e}")

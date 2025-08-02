import logging
import os
from sqlalchemy.orm import Session
from typing import List, Optional, Any
import uuid
import json
# import tiktoken
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
            logger.info(f"The  tool name is: : {name}")
            node.data.setdefault("tool_inputs", {})
            if not name:
                continue

            node.data.setdefault("tool_inputs", {})

            # always inject the user prompt if present
            if payload.prompt:
                node.data["tool_inputs"]["prompt"] = payload.prompt

            # CSV
            if name in ("CsvSearchTool", "CSV Query Tool") and payload.file_path:
                node.data["tool_inputs"]["file_path"] = payload.file_path

            # PDF Query Tool
            elif name == "PdfSearchTool" and payload.file_path:
                node.data["tool_inputs"]["file_path"] = payload.file_path

            # TranscribeAudioTool
            elif name in ("Transcribe Audio", "TranscribeAudioTool") and payload.file_path:
                node.data["tool_inputs"]["file_path"] = payload.file_path

            # RAG Tool
            elif name in ("RagTool", "File Query Tool"):
                # prefer explicit file_name, else fallback to basename of file_path
                if getattr(payload, "file_name", None):
                    node.data["tool_inputs"]["file_name"] = payload.file_name
                    node.data["tool_inputs"]["prompt"] = payload.prompt
                elif payload.file_path:
                    node.data["tool_inputs"]["file_name"] = os.path.basename(payload.file_path)

            #File readTool
            elif name == "FILEReaderTool" and payload.file_path:
                logger.info(f"Injecting form data into FILEReaderTool at node {node.id}")
                node.data["tool_inputs"]["form_data"] = payload.form_file_path

            #Serper Tool
            elif name == "Serper Search Tool":
                logger.info(f"Injecting prompt data into Serper tool at node {node.id}")
                node.data["tool_inputs"]["search_query"] = payload.prompt                

        # hand off to your builder
        builder = CrewBuilder(workflow.nodes)
        result = builder.build_and_run(payload)
        return schema.WorkflowExecutionResult(
            workflow_id=workflow_id, status="success", output=str(result)
        )
    except Exception as e:
        logger.info(f"error at running workflow:{e}")
    

def run_credit_card_workflow(db: Session,data: dict = None):
    workflow_id = uuid.UUID("095e3a52-85df-4037-ab04-c95dd646976d")
    logger.info(f"Running workflow with workflow_id: {workflow_id}")
    # Retrieve the workflow from DB
    workflow = get_workflow(db, workflow_id)
    if not workflow:
        raise ValueError(f"Workflow {workflow_id} not found")

    # Minimal payload just to satisfy the workflow structure
    class WorkflowPayload:
        def __init__(self, form_data_json):
            self.form_data = form_data_json
            self.prompt = None
            self.file_path = None
            self.file_name = None

    payload = WorkflowPayload(data)  # Safe default
    logger.info(f"The payload is{[payload]}")
    workflow = get_workflow(db, workflow_id)
    logger.info(f"The workflow is{[workflow]}")
    if not workflow:
        raise ValueError(f"Workflow {workflow_id} not found")

    # Inject only if data was provided
    if data:
        for node in workflow.nodes:
            task_name = node.data.get("task_name")

            if task_name == "Data collection":
                logger.info(f"Injecting form data into 'Data collection' task at node {node.id}")
                node.data.setdefault("tool_inputs", {})
                node.data["tool_inputs"]["form_data"] = payload.form_data

                node.data["task_description"] += (
                    f"\n\nUser Form Data:\n{payload.form_data}\n"
                )

            # elif task_name == "Data validator":
            #     logger.info(f"Injecting both form and PDF data into 'Data validator' task at node {node.id}")
            #     node.data.setdefault("tool_inputs", {})
            #     node.data["tool_inputs"]["form_data"] = payload.form_data
            #     node.data["tool_inputs"]["pdf_data"] = getattr(payload, "pdf_data", "")

            #     node.data["task_description"] += (
            #         "\n\nCompare the following data:\n"
            #         f"Form Data (user-submitted):\n{payload.form_data}\n\n"
            #         f"PDF Extracted Data:\n{getattr(payload, 'pdf_data', '')}\n"
            #         "\nIf the data does not match, explain what doesn't and ask user to re-apply."
            #     )

    builder = CrewBuilder(workflow.nodes)
    result = builder.build_and_run(payload)

    logger.info("Workflow executed successfully.")
    return schema.WorkflowExecutionResult(
        workflow_id=workflow_id, status="success", output=str(result)
    )

def run_data_comparison_workflow(db: Session, person_data_list: list[dict]):
    workflow_id = uuid.UUID("202342ae-0086-49f0-8a44-2a4ab25b2ae9")
    logger.info(f"Running workflow with workflow_id: {workflow_id}")

    workflow = get_workflow(db, workflow_id)
    if not workflow:
        raise ValueError(f"Workflow {workflow_id} not found")

    class WorkflowPayload:
        def __init__(self, person_data):
            self.person_data = person_data
            self.prompt = None
            self.file_path = None
            self.file_name = None

    payload = WorkflowPayload(person_data_list)

    for node in workflow.nodes:
        task_name = node.data.get("task_name")

        if task_name == "Data comparision":
            logger.info(f"Injecting person data into 'Data comparision' task at node {node.id}")
            node.data.setdefault("tool_inputs", {})
            node.data["tool_inputs"]["person_data"] = payload.person_data
            node.data["task_description"] += (
                f"\n\nCompare the following old and new data for each person:\n{json.dumps(payload.person_data, indent=2)}"
            )

    builder = CrewBuilder(workflow.nodes)
    result = builder.build_and_run(payload)

    logger.info("Workflow executed successfully.")
    return schema.WorkflowExecutionResult(
        workflow_id=workflow_id, status="success", output=str(result)
    )
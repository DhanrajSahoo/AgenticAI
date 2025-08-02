from fastapi import APIRouter, HTTPException, Depends, Form, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import uuid
# import tiktoken
from datetime import datetime
import os
from tavily import TavilyClient
import re
# from bs4 import BeautifulSoup
# from googlesearch import search
import requests
from db.vector_embeddings import Embeddings
import logging
import io
from pypdf import PdfReader
import json
import io
import pandas as pd
from pypdf import PdfReader
from schemas import workflows_schema as schema
from services import workflow_service
from services.crew_builder import CrewBuilderError
from db.database import get_db_session
from schemas.tools_schema import SemanticSearch
from services.aws_services import CloudWatchLogHandler

embed = Embeddings()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = CloudWatchLogHandler('agentic-ai', 'agentic-ai')
logger.addHandler(handler)

router = APIRouter(
    prefix="/workflows",
    tags=["Workflows"]
)


@router.post("/", response_model=schema.WorkflowResponse, status_code=201)
async def api_create_workflow(
        payload: schema.WorkflowCreatePayload,
        db: Session = Depends(get_db_session)
):
    try:
        return workflow_service.create_workflow(db=db, workflow_data_content=payload.data)
    except Exception as e:
        logger.error(f"Error creating workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")


@router.post("/list", response_model=List[schema.WorkflowResponse])
async def api_list_workflows(
        payload: schema.WorkflowListPayload,
        db: Session = Depends(get_db_session)
):
    try:
        return workflow_service.list_workflows(db=db, payload=payload)
    except Exception as e:
        logger.error(f"Error listing workflows: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list workflows.")


@router.post("/details", response_model=schema.WorkflowResponse)
async def api_get_workflow(
        payload: schema.WorkflowDetailPayload,
        db: Session = Depends(get_db_session)
):
    db_workflow = workflow_service.get_workflow(db=db, workflow_id=payload.workflow_id)
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
            db=db, workflow_id=workflow_id, workflow_update_data=workflow_data.data
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
async def api_run_workflow(payload:SemanticSearch,
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
        return workflow_service.run_workflow_service(payload, db=db, workflow_id=workflow_id)
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
    
@router.post("/bread_usecase", status_code=200)
async def api_run_breadusecase(
    full_name: str = Form(...),
    date_of_birth: str = Form(...),
    social_security_number: str = Form(...),
    street_no: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    zip_code: str = Form(...),
    residential_status: str = Form(...),
    current_address_length: str = Form(...),
    email: str = Form(...),
    mobile: str = Form(...),
    employment_status: str = Form(...),
    annual_income: str = Form(...),
    monthly_housing_payment: str = Form(...),
    credit_score: str = Form(...),
    total_credit_used: str = Form(...),
    deliquencies: str = Form(...),
    bankrupties: str = Form(...),
    monthly_debt_payments: str = Form(...),
    total_credit_limit: str = Form(...),
    files: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db_session)
):
    logger.info("Received form submission.")

    # Read and extract text from PDF
    file_content = files.file.read()
    pdf_stream = io.BytesIO(file_content)
    reader = PdfReader(pdf_stream)
    pdf_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    # pdf_text_lower = pdf_text.lower()

    # Construct form data for workflow later
    form_data = {
        "full_name": full_name,
        "date_of_birth": date_of_birth,
        "ssn": social_security_number,
        "address": street_no,
        "email": email,
        "mobile": mobile,
        "employment_status": employment_status,
        "income": annual_income,
        "monthly_debt_payments": monthly_debt_payments,
        "monthly_housing_payment": monthly_housing_payment,
        "Credit_Score": credit_score,
        "Total_credit_used": total_credit_used,
        "Total_credit_Limit": total_credit_limit,
        "Deliquencies": deliquencies,
        "Bankrupties": bankrupties,
        "city": city,
        "state": state,
        "zip_code": zip_code,
        "residential_status": residential_status,
        "current_address_length": current_address_length,
    }

    def field_in_pdf(pdf_text: str, value: str, possible_labels: list) -> bool:
        """
        Check if the value is present near any of the possible field labels in the pdf_text.
        """
        text = pdf_text.lower()
        value = value.lower().strip()

        for label in possible_labels:
            pattern = rf"{label}[^a-zA-Z0-9]{{0,10}}{re.escape(value)}"
            if re.search(pattern, text):
                return True
        return False
    # 🔍 Manual Validation (can be enhanced with fuzzy matching, NLP, etc.)
    mismatches = []

    if not field_in_pdf(pdf_text, full_name, ["name", "full name", "firstname", "applicant name"]):
        mismatches.append("full_name")

    if not field_in_pdf(pdf_text, date_of_birth, ["dob", "date of birth", "birth date"]):
        mismatches.append("date_of_birth")

    if not field_in_pdf(pdf_text, social_security_number, ["ssn", "social security number", "social_security_number"]):
        mismatches.append("ssn")

    # Optional address check (simple)
    # address_check = f"{street_no} {city}".lower()
    # if address_check not in pdf_text.lower().replace("\n", " "):
    #     mismatches.append("address")

    if mismatches:
        logger.warning(f"Form and document mismatch in fields: {mismatches}")
        return {
            "Workflow_id": "095e3a52-85df-4037-ab04-c95dd646976d",
            "status":"success",
            "output": f"Validation failed. The {', '.join(mismatches)} fields do not match the uploaded document.",
            "error": "null"
        }

    logger.info(f"PDF Validation Passed. Extracted PDF data: {pdf_text}")
    logger.info(f"Form Data Received: {form_data}")
    
    form_data_json = json.dumps(form_data)

    try:
        result = workflow_service.run_credit_card_workflow(data=form_data_json, db=db)
        return result
    except Exception as e:
        logger.exception("Error during workflow execution.")
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/Default_tracker", status_code=200)
async def api_run_Defaulterusecase(
    username: str = Form(...),
    user_email: str = Form(...),
    token: str = Form(...),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db_session)
):
    if not file:
        return {"status": "error", "message": "File is required."}

    logger.info("Received form.")
    content = await file.read()
    df = pd.read_excel(io.BytesIO(content))
    logger.info(f"Excel data received with {len(df)} rows.")
    total_contacts = len(df)
    person_data_list = []

    def gather_info(company: str, name: str, status: str) -> dict:
        return {'name': name, 'company': company, 'status': status}

    def gather_info_tavily(company: str, name: str) -> dict:
        try:
            client = TavilyClient(api_key='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')
            query = f"All professional and personal information about person {name}, who previously worked in {company}"
            result = client.search(query, search_depth="advanced", max_results=10)
            return result
        except Exception as e:
            logger.warning(f"Tavily error: {e}")
            return {}

    for _, row in df.iterrows():
        name = row.get("name") or row.get("Contact Name")
        company = row.get("company") or row.get("Company name")
        email = row.get("email") or row.get("Email")
        title = row.get("title") or row.get("Designation", "Unknown")

        old_data = gather_info(company, name, title)
        new_data = gather_info_tavily(company, name)

        person_data_list.append({
            "name": name,
            "email": email,
            "company": company,
            "title": title,
            "old_data": old_data,
            "new_data": new_data
        })

    result = workflow_service.run_data_comparison_workflow(db=db, person_data_list=person_data_list)

    if result.status == "success" and result.output:
        try:
            raw_output = result.output.strip()
            cleaned_output = re.sub(r"^```json\s*|\s*```$", "", raw_output)
            output_data = json.loads(cleaned_output)

            changes_data = output_data.get("changes_data", [])
            changes_detected = sum(1 for item in changes_data if item.get("Status") == "Changed")

            summary_data = {
                "total_contacts": str(total_contacts),
                "changes_detected": str(changes_detected),
                "pending_notifications": str(0),
                "last_import": datetime.now().strftime("%Y-%m-%d %H:%M")
            }

            # ✅ Convert `output` dict to a JSON string to match frontend expectations
            stringified_output = json.dumps({
                "summary_data": summary_data,
                "changes_data": changes_data
            })

            return {
                "workflow_id": result.workflow_id,
                "status": "success",
                "output": stringified_output,  # ✅ frontend-compatible format
                "error": None
            }

        except Exception as e:
            logger.error(f"Error parsing output JSON: {e}")
            return {
                "workflow_id": getattr(result, "workflow_id", None),
                "status": "failed",
                "output": None,
                "error": "Internal error while parsing workflow output."
            }

    else:
        return {
            "workflow_id": getattr(result, "workflow_id", None),
            "status": "failed",
            "output": None,
            "error": getattr(result, "error", "Unknown error")
        }
 



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
        "monthly_housing_payment":monthly_housing_payment,
        "Credit_Score":credit_score,
        "Total_credit_used":total_credit_used,
        "Total_credit_Limit":total_credit_limit,
        "Deliquencies":deliquencies,
        "Bankrupties":bankrupties,
        "city":city,
        "state":state,
        "zip_code":zip_code,
        "residential_status":residential_status,
        "current_address_length":current_address_length,
    }
    file_content = files.file.read()  # Read file content as bytes
    pdf_stream = io.BytesIO(file_content)  # Wrap in a binary stream
    reader = PdfReader(pdf_stream)  # Use PyPDF reader

    pdf_text = "\n".join(page.extract_text() or "" for page in reader.pages)


    logger.info(f"validation data is:{pdf_text}")
    logger.info(f"Form Data Received: {form_data}")
    form_data_json = json.dumps(form_data)
    # Identity_proof = file.
    try:
        logger.info("Running workflow with DB-stored payload (ignoring form data for now).")
        # ✅ Currently we ignore form_data in workflow run, but keep it available here
        result = workflow_service.run_credit_card_workflow(data=form_data_json,pdf_data=pdf_text, db=db)
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
    # logger.info(f"Excel data received with {len(df)} rows.")

    person_data_list = []

    def gather_info(company: str, name: str, status: str) -> dict:
        # query = f"'{name}' '{company}' '{status}'"
        # urls = []
        profile = {'name': name, 'company': company, 'status': status}
        # for url in search(query):
        #     if url.startswith("https"):
        #         urls.append(url)
        #     if len(urls) >= 5:
        #         break
        # for url in urls:
        #     try:
        #         r = requests.get(url, timeout=5)
        #         soup = BeautifulSoup(r.text, 'html.parser')
        #         data = {'url': url, 'data': []}
        #         for p in soup.find_all('p'):
        #             text = p.get_text(strip=True)
        #             if text:
        #                 clean = re.sub(r'\s+', ' ', text)
        #                 data['data'].append(clean)
        #         profile['url_data'].append(data)
        #     except Exception as e:
        #         logger.warning(f"Error scraping {url}: {e}")
        return profile

    def gather_info_tavily(company: str, name: str) -> dict:
        try:
            client = TavilyClient(api_key='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')
            query = f"All professional and personal information about person {name}, who previously worked in {company}"
            result = client.search(query, search_depth="advanced", max_results=10)
            # logger.info(f"The result from Tavily is{result}")
            return result
        except Exception as e:
            logger.warning(f"Tavily error: {e}")
            return {}

    for _, row in df.iterrows():
        name = row.get("name") or row.get("Contact Name")
        company = row.get("company") or row.get("Company name")
        email = row.get("email") or row.get("Email")
        title = row.get("title") or row.get("Designation", "Unknown")
        # logger.info(f"Processing: {name}, {company}, {title}")

        old_data = gather_info(company, name, title)
        # logger.info(f"The old data is{old_data}")
        new_data = gather_info_tavily(company, name)

        person_data_list.append({
            "name": name,
            "email": email,
            "company": company,
            "title": title,
            "old_data": old_data,
            "new_data": new_data
        })

        logger.info(f"The person data list is{person_data_list}")

    # summary = summary["pending_notifications"] = len(person_data_list)

    # Inject into the Crew workflow
    result = workflow_service.run_data_comparison_workflow(db=db, person_data_list=person_data_list)

    return result
    # Assuming result follows: { workflow_id, status, output, error }
    # if result.status == "success" and result.output:
    #     try:
    #         output_data = json.loads(result.output)
    #         return {
    #            result.output
    #         }
    #     except Exception as e:
    #             logger.error(f"Error parsing output JSON: {e}")
    #             return {
    #                 "status": "failed",
    #                 "message": "Internal error while parsing workflow output."
    #             }
    # else:
    #     return {
    #     "status": "failed",
    #     "message": result.error or "Unknown workflow error."
    # }


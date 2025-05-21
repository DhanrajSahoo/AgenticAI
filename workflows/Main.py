from fastapi import FastAPI, Depends, HTTPException
from DB_conn import get_db, Workflow, Tool
from data import workflow_data
from sqlalchemy.orm import Session
import json
import logging
import datetime
import uuid
from crewai import Task, tools, Agent, Crew
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI()
# workflow_dummy = {}

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# ==================Pydantic for Tools===========================
class ToolBase(BaseModel):
    tool_name: str
    tool_description: str
    parameters: dict

class ToolResponse(ToolBase):
    tool_id: str  # Changed to str to match TEXT in SQLAlchemy
    tool_name: str
    tool_description: Optional[str]
    parameters: dict
    created_at: datetime.datetime
    updated_at: datetime.datetime

class ToolCreate(ToolBase):
    pass

class ToolUpdate(ToolBase):
    tool_name: Optional[str] = None
    tool_description: Optional[str] = None
    parameters: Optional[dict] = None

# ==================Pydantic for Workflow===========================


class WorkflowBase(BaseModel):
    name: str
    definition: dict

class WorkflowCreate(WorkflowBase):
    pass

class WorkflowUpdate(WorkflowBase):
    name: Optional[str] = None
    definition: Optional[dict] = None

class WorkflowResponse(WorkflowBase):
    workflows_id: uuid.UUID
    name: str
    definition: dict
    created_at: datetime.datetime
    updated_at: datetime.datetime

#--------------------TOOLS CRUD--------------------------


@app.get("/tools/{tool_id}", response_model=ToolResponse)
def read_tool(tool_id: str, db: Session = Depends(get_db)):
    """
    Get a tool by its ID.
    """
    db_tool = db.query(Tool).filter(Tool.tool_id == tool_id).first()
    if not db_tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return db_tool

@app.get("/tools/", response_model=List[ToolResponse])
def read_tools(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get all tools.
    """
    db_tools = db.query(Tool).offset(skip).limit(limit).all()
    return db_tools


@app.delete("/tools/{tool_id}", response_model=dict)
def delete_tool(tool_id: str, db: Session = Depends(get_db)
):
    """
    Delete a tool by its ID.
    """
    db_tool = db.query(Tool).filter(Tool.tool_id == tool_id).first()
    if not db_tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    db.delete(db_tool)
    db.commit()
    return {"message": "Tool deleted successfully"}


# -------------- CRUD Operations for Workflows ------------------

@app.post("/workflows/", response_model=WorkflowResponse, status_code=201)
def create_workflow(request_body: dict, db: Session = Depends(get_db)):
    """
    Create and save a new workflow.
    """
    workflow_id = str(uuid.uuid4())
    try:
        workflow_payload = request_body.get("workflow")
        if not workflow_payload:
            raise HTTPException(status_code=422, detail="Missing 'workflow' key in request body")

        workflow_create = WorkflowCreate(**workflow_payload)  # Pass the inner dictionary
        db_workflow = Workflow(
            workflows_id=workflow_id,
            name=workflow_create.name,
            definition=workflow_create.definition,
        )
        db.add(db_workflow)
        db.commit()
        db.refresh(db_workflow)
        logger.debug(f"db_workflow after refresh: {db_workflow.__dict__}")
        return db_workflow
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid data format: {e}")
    
@app.get("/workflows/", response_model=List[WorkflowResponse])
def get_all_workflows(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get all workflows.
    """
    workflows = db.query(Workflow).offset(skip).limit(limit).all()
    return workflows

@app.get("/workflows/{workflow_id}")
def get_workflow_by_id(workflow_id: str, db: Session = Depends(get_db)):
    """
    Get a workflow by its ID.
    """
    db_workflow = (
        db.query(Workflow).filter(Workflow.workflows_id == workflow_id).first()
    )
    if not db_workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return db_workflow

@app.put("/workflows/{workflow_id}")
def update_workflow(workflow_id: uuid.UUID, workflow: WorkflowUpdate, db: Session = Depends(get_db)):
    """
    Update a workflow by its ID.
    """
    db_workflow = db.query(Workflow).filter(Workflow.workflows_id == workflow_id).first()
    if not db_workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    for key, value in workflow.dict().items():
        setattr(db_workflow, key, value)
    db.commit()
    db.refresh(db_workflow)
    return db_workflow

@app.delete("/workflows/{workflow_id}", response_model=dict)
def delete_workflow(workflow_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Delete a workflow by its ID.
    """
    db_workflow = db.query(Workflow).filter(Workflow.workflows_id == workflow_id).first()
    if not db_workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    db.delete(db_workflow)
    db.commit()
    return {"message": "Workflow deleted successfully"}


# --- Endpoint to Run CrewAI  ---
@app.post("/workflows/{workflow_id}/run")
async def run_crewai(workflow_id: uuid.UUID, db: Session = Depends(get_db)):
    '''
    Retrive the workflow by workflow_id and run the crew-kickoff
    
    '''
    workflow_id = str(workflow_id)
    db_workflow = db.query(Workflow).filter(Workflow.workflows_id == workflow_id).first()
    if not db_workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    try:
        definition = db_workflow.definition
        nodes = definition.get("nodes", [])
        # edges = definition.get("edges", [])

        print(nodes)
        agent_map = {}
        for node in nodes:
            if node["data"]["label"] == "Agent":
                agent = Agent(
                    role=node["meta"]["agent_name"],
                    goal=node["meta"]["agent_goal"],
                    backstory=node["meta"]["agent_backstory"],
                    model=node["meta"]["agent_model"]
                )
                agent_map[node["id"]] = agent

        tasks = []
        for node in nodes:
            if node["data"]["label"] == "Task":
                source_agent_id = node["source"][0] if node["source"] else None
                if source_agent_id and source_agent_id in agent_map:
                    task = Task(
                        description=node["meta"]["task"],
                        agent=agent_map[source_agent_id]
                    )
                    tasks.append(task)

        agents = list(agent_map.values())

        crew = Crew(
            agents=agents,
            tasks=tasks,
            verbose=True
        )



    #     return {"The crew has been executed" : "SUCCESS",
    #             "result": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
     

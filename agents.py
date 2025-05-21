# agents.py (or views.py if combined)

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from my_agent import MyAgent
from db_utils import save_agent, load_agents, delete_agent

router = APIRouter()

# ---------- SCHEMAS ----------

class ToolInput(BaseModel):
    tool_id: str

class AgentCreate(BaseModel):
    role: str
    backstory: str
    goal: str
    allow_delegation: bool = True
    verbose: bool = True
    cache: bool = True
    llm_provider_model: Optional[str] = None
    temperature: Optional[float] = 0.5
    max_iter: Optional[int] = 5
    user_email: str
    tools: List[ToolInput] = []
    knowledge_source_ids: Optional[List[str]] = []

class AgentUpdate(BaseModel):
    role: str
    user_email: str
    goal: Optional[str] = None
    backstory: Optional[str] = None
    llm_provider_model: Optional[str] = None
    temperature: Optional[float] = None

class AgentDelete(BaseModel):
    role: str
    user_email: str

# ---------- ROUTES ----------

@router.post("/api/agent")
def create_agent(agent_data: AgentCreate):
    agent = MyAgent(
        role=agent_data.role,
        backstory=agent_data.backstory,
        goal=agent_data.goal,
        allow_delegation=agent_data.allow_delegation,
        verbose=agent_data.verbose,
        cache=agent_data.cache,
        llm_provider_model=agent_data.llm_provider_model,
        temperature=agent_data.temperature,
        max_iter=agent_data.max_iter,
        tools=[],  # tools added below
        knowledge_source_ids=agent_data.knowledge_source_ids,
        user_email=agent_data.user_email
    )
    save_agent(agent)
    return {"status": "Agent created successfully", "agent_id": agent.id}


@router.put("/api/agent")
def update_agent(update_data: AgentUpdate):
    agents = load_agents()
    agent = next((a for a in agents if a.role == update_data.role and a.user_email == update_data.user_email), None)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if update_data.goal: agent.goal = update_data.goal
    if update_data.backstory: agent.backstory = update_data.backstory
    if update_data.llm_provider_model: agent.llm_provider_model = update_data.llm_provider_model
    if update_data.temperature is not None: agent.temperature = update_data.temperature

    save_agent(agent)
    return {"status": "Agent updated successfully"}


@router.delete("/api/agent")
def delete_agent_view(payload: AgentDelete):
    agents = load_agents()
    agent = next((a for a in agents if a.role == payload.role and a.user_email == payload.user_email), None)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    delete_agent(agent.id)
    return {"status": "Agent deleted successfully"}

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from my_agent import MyAgent
from db_utils import save_agent, load_agents, delete_agent

router = APIRouter()

class AgentPayload(BaseModel):
    user_email: str
    role: str
    backstory: Optional[str] = ""
    goal: Optional[str] = ""
    allow_delegation: Optional[bool] = False
    verbose: Optional[bool] = True
    cache: Optional[bool] = True
    llm_provider_model: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_iter: Optional[int] = 5
    tools: Optional[List[str]] = []

@router.post("/create-agent")
def create_agent(payload: AgentPayload):
    agent = MyAgent(
        user_email=payload.user_email,
        role=payload.role,
        backstory=payload.backstory,
        goal=payload.goal,
        allow_delegation=payload.allow_delegation,
        verbose=payload.verbose,
        cache=payload.cache,
        llm_provider_model=payload.llm_provider_model,
        temperature=payload.temperature,
        max_iter=payload.max_iter,
        tools=payload.tools,
        created_at=datetime.now().isoformat()
    )
    save_agent(agent)
    return {"message": "Agent created successfully", "agent_id": agent.id}

@router.put("/update-agent")
def update_agent(payload: AgentPayload):
    agents = load_agents()
    agent = next((a for a in agents if a.user_email == payload.user_email and a.role == payload.role), None)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent.backstory = payload.backstory
    agent.goal = payload.goal
    agent.allow_delegation = payload.allow_delegation
    agent.verbose = payload.verbose
    agent.cache = payload.cache
    agent.llm_provider_model = payload.llm_provider_model
    agent.temperature = payload.temperature
    agent.max_iter = payload.max_iter
    agent.tools = payload.tools
    save_agent(agent)
    return {"message": "Agent updated successfully"}

@router.delete("/delete-agent")
def delete_agent_api(user_email: str, role: str):
    agents = load_agents()
    agent = next((a for a in agents if a.user_email == user_email and a.role == role), None)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    delete_agent(agent.id)
    return {"message": "Agent deleted successfully"}

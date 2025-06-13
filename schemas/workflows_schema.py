from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator, UUID4, EmailStr
from datetime import datetime


class UIRawNodeData(BaseModel):
    # This will act as a container for various data shapes
    class Config:
        extra = 'allow'

class UIAgentNodeData(UIRawNodeData):
    agent_name: str = Field(default="New Agent")
    agent_role: str = Field(default="Default Role")
    agent_goal: str = Field(default="Default Goal")
    agent_backstory: str = Field(default="Default Backstory")
    agent_model: Optional[str] = None
    agent_temprature: Optional[float] = Field(default=0.7, ge=0.0, le=1.0) # Matches UI typo
    agent_iteration: Union[str, int] = Field(default=25) # Allow string, will parse in builder
    agent_delegation: bool = False
    agent_verbose: bool = False
    agent_cache: bool = True

class UITaskNodeData(UIRawNodeData):
    task_name: str = Field(default="New Task")
    task_description: str = Field(default="Default Task Description")
    task_expected_op: str = Field(default="Default Expected Output", alias="task_expected_op")

class UIToolNodeData(UIRawNodeData):
    tool_name: str # This is the tool_id from the registry, e.g., "serper_dev_tool"
    config_params: Optional[Dict[str, Any]] = None # Parameters for this tool instance

# UI Node Structure
class UINode(BaseModel):
    id: str
    data: Dict[str, Any]
    position: Dict[str, float]
    parents: List[str] = Field(default_factory=list)
    childs: List[str] = Field(default_factory=list)
    source: List[str] = Field(default_factory=list)

# Workflow API Payloads
class WorkflowDataContent(BaseModel):
    workflow_name: str
    workflow_description: str
    nodes: List[UINode]

class WorkflowCreatePayload(BaseModel):
    token: str
    user_name: Optional[str] = ""
    user_email: Optional[EmailStr] = ""
    data: WorkflowDataContent

class WorkflowUpdatePayload(BaseModel):
    token: str
    user_name: Optional[str] = ""
    user_email: Optional[EmailStr] = ""
    data: WorkflowDataContent

# Workflow Response Model
class WorkflowResponse(BaseModel):
    id: UUID4
    workflow_name: str
    workflow_description: str
    nodes: List[UINode]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Workflow Execution
class WorkflowExecutionResult(BaseModel):
    workflow_id: UUID4
    status: str
    output: Optional[Any] = None
    error: Optional[str] = None


class WorkflowListPayload(BaseModel):
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=200)  # todo: discuss max limit with team


class WorkflowDetailPayload(BaseModel):
    workflow_id: UUID4
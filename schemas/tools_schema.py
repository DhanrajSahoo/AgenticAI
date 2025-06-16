from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal, List


class ToolParameterDetail(BaseModel):
    type: Literal["text", "number", "boolean", "fileupload", "textarea"] = "text"
    label: str
    required: bool = False
    default: Optional[Any] = None
    description: Optional[str] = None
    options: Optional[List[str]] = None
    accept: Optional[str] = None  # todo: possible change for different input type For fileupload, e.g., ".json,.csv"


class ToolDefinition(BaseModel):
    numeric_id: int
    original_id: str
    name: str
    description: str
    class_name: Optional[str] = None
    parameters_schema: Optional[Dict[str, ToolParameterDetail]] = None

class FileCreate(BaseModel):
    file_name: str
    file_url: str

class FileQuery(BaseModel):
    file_name: Optional[str] = None

class FileDelete(BaseModel):
    file_name : str

class SemanticSearch(BaseModel):
    prompt : str
    vector_search_engine: str

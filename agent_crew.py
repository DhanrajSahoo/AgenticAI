import logging
from typing import Optional, List, Dict, Any

from crewai import Agent as CrewAgent
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class AgentModel(BaseModel):
    """
    A model representing an AI agent, compatible with CrewAI.
    """
    id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Agent display name")
    role: str = Field(..., description="What this agent is responsible for")
    goal: str = Field(..., description="The mission of the agent")
    backstory: str = Field(..., description="Backstory to help guide agent behavior")
    tools: Optional[List[str]] = Field(default_factory=list, description="Tool IDs")
    verbose: bool = Field(default=False, description="Enable verbose mode")
    llm_config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="LLM configuration")

    @field_validator("role", "goal", "backstory")
    @classmethod
    def validate_non_empty(cls, value, info):
        if not value.strip():
            raise ValueError(f"{info.field_name.capitalize()} must not be empty.")
        return value

    def _build_llm(self):
        if not self.llm_config:
            return None

        model = self.llm_config.get("model", "gpt-4")
        temperature = self.llm_config.get("temperature", 0.7)
        max_tokens = self.llm_config.get("max_tokens", 1024)

        try:
            llm = ChatOpenAI(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
            logger.info(f"Created LLM instance for agent '{self.id}' using model '{model}'")
            return llm
        except Exception as e:
            logger.exception(f"Failed to initialize LLM for agent '{self.id}': {e}")
            raise

    def to_crewai_agent(self, tool_objects: Optional[dict] = None) -> CrewAgent:
        """
        Convert to CrewAI Agent instance.
        """
        logger.info(f"Creating CrewAI Agent from AgentModel '{self.id}'")

        tools = []
        if self.tools and tool_objects:
            for tool_id in self.tools:
                tool = tool_objects.get(tool_id)
                if not tool:
                    logger.warning(f"Tool '{tool_id}' not found.")
                else:
                    tools.append(tool)

        llm = self._build_llm()

        try:
            agent = CrewAgent(
                name=self.name,
                role=self.role,
                goal=self.goal,
                backstory=self.backstory,
                tools=tools,
                verbose=self.verbose,
                llm=llm
            )
            logger.info(f"Successfully created agent '{self.id}'")
            return agent
        except Exception as e:
            logger.exception(f"Failed to create CrewAI agent '{self.id}': {e}")
            raise



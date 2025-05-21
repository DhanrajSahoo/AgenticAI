import logging
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, field_validator
from crewai import Task as CrewTask
from crewai import Agent

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class TaskModel(BaseModel):
    """
    A model representing a task in the agentic workflow,
    designed to work with CrewAI's Task abstraction.
    """
    id: str = Field(..., description="Unique identifier for the task")
    description: str = Field(..., description="A clear description of the task")
    expected_output: Optional[str] = Field(None, description="The expected output or deliverable")
    agent_ids: List[str] = Field(..., description="List of agent IDs associated with the task")

    @field_validator("agent_ids")
    @classmethod
    def validate_agent_ids(cls, value):
        if not value:
            raise ValueError("At least one agent_id must be provided for a task.")
        return value

    def to_crewai_task(self, agents_dict: Dict[str, Agent]) -> CrewTask:
        """
        Converts this TaskModel into a CrewAI Task with multiple agents.
        Args:
            agents_dict (Dict[str, Agent]): A dictionary of Agent instances keyed by their IDs.
        Returns:
            CrewTask: A CrewAI Task instance configured with the associated agents.
        Raises:
            ValueError: If any agent_id is not found in agents_dict.
        """
        logger.info(f"Converting TaskModel '{self.id}' to CrewAI Task...")

        missing_agents = [agent_id for agent_id in self.agent_ids if agent_id not in agents_dict]
        if missing_agents:
            error_msg = f"Missing agents in agents_dict: {missing_agents}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        agents = [agents_dict[agent_id] for agent_id in self.agent_ids] #todo: based on agentID create agent
        logger.debug(f"Agents assigned to task '{self.id}': {[a.role for a in agents]}")

        try:
            crewai_task = CrewTask(
                description=self.description,
                expected_output=self.expected_output,
                agent=agents
            )
            logger.info(f"Successfully created CrewAI Task for '{self.id}'")
            return crewai_task

        except Exception as e:
            logger.exception(f"Failed to create CrewAI Task for '{self.id}': {e}")
            raise


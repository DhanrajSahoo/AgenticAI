import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from pydantic import ValidationError
import os

from schemas import workflows_schema as ui_schema
from tool_registry.registry import get_tool_instance
from core.config import settings

from core.config import Config,db_cred

from tool_registry.tool_wrappers import StaticInputToolWrapper

os.environ["OPENAI_API_KEY"] = Config.openai_key
os.environ["AWS_ACCESS_KEY_ID"] = db_cred.get("access_key")
os.environ["AWS_SECRET_ACCESS_KEY"] = db_cred.get("secret_key")
os.environ["AWS_REGION"] = "us-east-1"
os.environ["SERPER_API_KEY"]


from crewai import Agent, Task, Crew, Process
from crewai import LLM as CrewLLM
from langchain_openai import ChatOpenAI
bedrock_model_prefixes = ["bedrock/anthropic.", "bedrock/amazon.", "bedrock/cohere."]

from services.aws_services import CloudWatchLogHandler

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = CloudWatchLogHandler('agentic-ai', 'agentic-ai')
logger.addHandler(handler)

class CrewBuilderError(Exception):
    pass


class CrewBuilder:
    def __init__(self, ui_nodes: List[ui_schema.UINode]):
        self.ui_nodes = ui_nodes
        self.nodes_map: Dict[str, ui_schema.UINode] = {
            node.id: node for node in self.ui_nodes
        }

        self.crew_agents: List[Agent] = []
        self.agent_node_to_instance_map: Dict[str, Agent] = {}
        self.task_node_to_instance_map: Dict[str, Task] = {}  # Stores Task instances
        self.ordered_crew_tasks: List[Task] = []

        if not settings.OPENAI_API_KEY:
            raise EnvironmentError("OPENAI_API_KEY is not set. CrewAI requires it.")

        self.default_llm = ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            model_name=settings.OPENAI_MODEL_NAME,
            temperature=0.7
        )

    def _get_node_type(self, node_id: str) -> Optional[str]:
        if node_id.startswith("agent-"):
            return "agent"
        elif node_id.startswith("task-"):
            return "task"
        elif node_id.startswith("tool-"):
            return "tool"
        return None

    def _instantiate_agents_with_tools(self):
        for ui_node in self.ui_nodes:
            if self._get_node_type(ui_node.id) == "agent":
                try:
                    agent_data = ui_schema.UIAgentNodeData.model_validate(ui_node.data)
                except ValidationError as e:
                    raise CrewBuilderError(f"Invalid data for agent node '{ui_node.id}': {e.errors()}")

                agent_tools = []
                for source_node_id in ui_node.source:
                    if self._get_node_type(source_node_id) == "tool":
                        tool_ui_node = self.nodes_map[source_node_id]

                        try:
                            tool_data = ui_schema.UIToolNodeData.model_validate(tool_ui_node.data)
                        except ValidationError as e:
                            raise CrewBuilderError(f"Invalid data for tool node '{tool_ui_node.id}': {e.errors()}")

                        # instantiate the tool class itself
                        base = get_tool_instance(tool_data.tool_name, tool_data.config_params)

                        # now pull _only_ the dict under "tool_inputs"
                        raw = tool_ui_node.data.get("tool_inputs")
                        tool_inputs = raw.copy() if isinstance(raw, dict) else {}

                        # if there really are inputs, wrap them
                        if tool_inputs:
                            try:
                                base = StaticInputToolWrapper(base, tool_inputs)
                            except Exception as e:
                                raise CrewBuilderError(
                                    f"Failed to wrap tool '{tool_data.tool_name}' with static inputs: {e}"
                                )

                        agent_tools.append(base)
                logger.info(f"agent_tools:{agent_tools}")

                agent_llm = self.default_llm
                if agent_data.agent_model and agent_data.agent_model.strip():
                    model_name = agent_data.agent_model.strip()

                    # Check if the model is a Bedrock modelx
                    if any(model_name.startswith(prefix) for prefix in bedrock_model_prefixes):
                        # Use CrewAI's LLM wrapper for Bedrock
                        agent_llm = CrewLLM(
                            model=model_name,
                            temperature=agent_data.agent_temprature or 0.7,
                            # config={
                            #     "aws_access_key_id": settings.access_key,
                            #     "aws_secret_access_key": settings.secret_key,
                            #     "region_name": 'us-east-1'
                            # }
                        )
                    else:
                        # Assume it's an OpenAI model
                        agent_llm = ChatOpenAI(
                            openai_api_key=Config.openai_key,
                            model_name=model_name,
                            temperature=agent_data.agent_temprature or 0.7
                        )

                # Handle agent_iteration
                agent_max_iter_val = 5
                if agent_data.agent_iteration is not None:
                    if isinstance(agent_data.agent_iteration, str):
                        try:
                            parsed_iter = int(agent_data.agent_iteration)
                            if parsed_iter >= 1:
                                agent_max_iter_val = parsed_iter
                            else:
                                print(
                                    f"Warning: agent_iteration '{agent_data.agent_iteration}' is not >= 1. Using default {agent_max_iter_val}.")
                        except ValueError:
                            print(
                                f"Warning: Could not convert agent_iteration string '{agent_data.agent_iteration}' to int. Using default {agent_max_iter_val}.")
                    elif isinstance(agent_data.agent_iteration, int):
                        if agent_data.agent_iteration >= 1:
                            agent_max_iter_val = agent_data.agent_iteration
                        else:
                            print(
                                f"Warning: agent_iteration {agent_data.agent_iteration} is not >= 1. Using default {agent_max_iter_val}.")

                agent = Agent(
                    role=agent_data.agent_role,
                    goal=agent_data.agent_goal,
                    backstory=agent_data.agent_backstory,
                    verbose=agent_data.agent_verbose,
                    allow_delegation=agent_data.agent_delegation,
                    tools=agent_tools,
                    llm=agent_llm,
                    max_iter=agent_max_iter_val,
                    cache=agent_data.agent_cache
                )
                logger.info(f"agent{agent}")
                self.crew_agents.append(agent)
                self.agent_node_to_instance_map[ui_node.id] = agent

    def _instantiate_tasks_and_map_agents(self) -> Dict[str, Dict[str, Any]]:
        """
        First pass: create Task instances and identify their assigned agent and raw context task IDs.
        Prioritizes 'parents' array for connections, falls back to 'source' if 'parents' is empty.
        Returns a dictionary of task configurations.
        """
        task_configs: Dict[str, Dict[str, Any]] = {}

        for ui_node in self.ui_nodes:
            if self._get_node_type(ui_node.id) == "task":
                try:
                    task_data = ui_schema.UITaskNodeData.model_validate(ui_node.data)
                except ValidationError as e:
                    raise CrewBuilderError(f"Invalid data for task node '{ui_node.id}': {e.errors()}")

                assigned_agent_instance: Optional[Agent] = None
                context_task_node_ids: List[str] = []

                # --- Start of the modified logic block ---
                # Prioritize parents for connections
                connection_candidates = ui_node.parents

                # If parents is empty, check source as a fallback
                # We use hasattr and check if ui_node.source is not empty to be robust
                if not connection_candidates and hasattr(ui_node, 'source') and ui_node.source:
                    connection_candidates = ui_node.source
                # --- End of the modified logic block ---

                # Now iterate through the determined list of connection candidates
                for connected_node_id in connection_candidates:
                    connected_node_type = self._get_node_type(connected_node_id)
                    if connected_node_type == "agent":
                        agent_instance = self.agent_node_to_instance_map.get(connected_node_id)
                        if not agent_instance:
                            raise CrewBuilderError(
                                f"Agent node '{connected_node_id}' for task '{ui_node.id}' not found or not instantiated."
                            )
                        assigned_agent_instance = agent_instance
                    elif connected_node_type == "task":
                        context_task_node_ids.append(connected_node_id)

                if not assigned_agent_instance:
                    if not self.crew_agents:
                        raise CrewBuilderError(
                            f"No agents defined in the workflow to assign to task '{task_data.task_name}'."
                        )
                    # Update the error message to clearly state both parents and source were checked
                    raise CrewBuilderError(
                        f"Task '{task_data.task_name}' (Node ID: {ui_node.id}) is not connected to an agent "
                        f"via its 'parents' array, and its 'source' array is also empty or does not contain an agent."
                    )

                task_configs[ui_node.id] = {
                    "description": task_data.task_description,
                    "expected_output": task_data.task_expected_op,
                    "agent_instance": assigned_agent_instance,
                    "context_task_node_ids": context_task_node_ids,
                }

        # Now create Task objects without context yet, so all task instances exist for context linking
        for ui_node_id, config in task_configs.items():
            task = Task(
                description=config["description"],
                expected_output=config["expected_output"],
                agent=config["agent_instance"]
                # `context` will be set in the next step
            )
            self.task_node_to_instance_map[ui_node_id] = task

        return task_configs

    def _resolve_task_dependencies_and_order(self, task_configs: Dict[str, Dict[str, Any]]):
        """
        Second pass: Set the `context` attribute for each Task instance and topologically sort them.
        """
        if not self.task_node_to_instance_map:
            return

        for ui_node_id, task_instance in self.task_node_to_instance_map.items():
            config = task_configs.get(ui_node_id)  # Get the raw config for this task
            if not config:  # Should not happen if logic is correct
                continue

            context_crewai_tasks: List[Task] = []
            for context_task_node_id in config["context_task_node_ids"]:
                context_task_instance = self.task_node_to_instance_map.get(context_task_node_id)
                if not context_task_instance:
                    raise CrewBuilderError(
                        f"Context task node '{context_task_node_id}' for task '{ui_node_id}' not found or not instantiated.")
                context_crewai_tasks.append(context_task_instance)

            task_instance.context = context_crewai_tasks  # Assign list of CrewAI Task objects for context

        # Topological sort
        prerequisites: Dict[str, Set[str]] = {
            tid: set(task_configs[tid]["context_task_node_ids"])
            for tid in self.task_node_to_instance_map.keys()  # Iterate over actual task instances
        }

        in_degree: Dict[str, int] = {tid: 0 for tid in self.task_node_to_instance_map.keys()}
        adj: Dict[str, List[str]] = {tid: [] for tid in self.task_node_to_instance_map.keys()}

        for task_id, prereqs_set in prerequisites.items():
            in_degree[task_id] = len(prereqs_set)
            for prereq_id in prereqs_set:
                if prereq_id not in self.task_node_to_instance_map:
                    raise CrewBuilderError(
                        f"Task '{task_id}' lists non-existent or non-task node '{prereq_id}' as a context/source.")
                adj[prereq_id].append(task_id)

        queue = [tid for tid, degree in in_degree.items() if degree == 0]

        while queue:
            task_id_to_add = queue.pop(0)
            self.ordered_crew_tasks.append(self.task_node_to_instance_map[task_id_to_add])

            for dependent_task_id in adj.get(task_id_to_add, []):
                in_degree[dependent_task_id] -= 1
                if in_degree[dependent_task_id] == 0:
                    queue.append(dependent_task_id)

        if len(self.ordered_crew_tasks) != len(self.task_node_to_instance_map):
            processed_task_ids = {task.description for task in self.ordered_crew_tasks}
            all_task_ids = {self.task_node_to_instance_map[tid].description for tid in self.task_node_to_instance_map}
            remaining_nodes = all_task_ids - processed_task_ids
            raise CrewBuilderError(
                f"Workflow has a cycle in task dependencies or invalid task structure. Could not order all tasks. Problematic task descriptions might be among: {remaining_nodes}")

    def _create_and_kickoff_crew(self) -> Any:
        if not self.crew_agents:
            return "Workflow has no agents defined. Cannot create a crew."
        if not self.ordered_crew_tasks:
            return "Workflow has agents but no executable tasks defined, processed, or ordered. Cannot create a crew."


        crew = Crew(
            agents=self.crew_agents,
            tasks=self.ordered_crew_tasks,  # Use the topologically sorted list
            process=Process.sequential,
            verbose=True
        )

        result = crew.kickoff()
        return result

    def build_and_run(self) -> Any:
        try:
            self._instantiate_agents_with_tools()

            if not any(self._get_node_type(n.id) == "task" for n in self.ui_nodes):
                if self.crew_agents:
                    logger.info(f"crew_agents:{self.crew_agents}")
                    return "Workflow has agents defined, but no tasks. A crew requires tasks to run."
                return "Workflow is empty or contains no tasks."

            raw_task_configs = self._instantiate_tasks_and_map_agents()  # Creates Task instances
            logger.info(f"raw_task_configs:{raw_task_configs}")

            if not self.task_node_to_instance_map:  # No Task instances were successfully created
                raise CrewBuilderError("Tasks were defined in the workflow, but none could be instantiated correctly.")

            self._resolve_task_dependencies_and_order(raw_task_configs)  # Sets context and orders
            return self._create_and_kickoff_crew()

        except CrewBuilderError as e:
            raise
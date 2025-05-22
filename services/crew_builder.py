from typing import List, Dict, Any, Optional, Set, Tuple
from pydantic import ValidationError
import os
import uuid

from schemas import workflows_schema as schema
from tool_registry.registry import get_tool_instance
from core.config import settings

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI


class CrewBuilder:
    def __init__(self, workflow_definition: schema.WorkflowInDB):
        self.workflow_def = workflow_definition
        self.nodes_map: Dict[str, schema.WorkflowNode] = {
            node.id: node for node in self.workflow_def.nodes
        }
        self.edges: List[schema.WorkflowEdge] = self.workflow_def.edges

        self.crew_agents: List[Agent] = []
        self.agent_node_to_instance_map: Dict[str, Agent] = {}
        self.task_node_to_instance_map: Dict[str, Task] = {}
        self.ordered_crew_tasks: List[Task] = []

        if not settings.OPENAI_API_KEY:
            raise EnvironmentError("OPENAI_API_KEY is not set. CrewAI requires it.")

        self.llm = ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            model_name=settings.OPENAI_MODEL_NAME
        )

    def _instantiate_agents_with_tools(self):
        for node_id, wf_node in self.nodes_map.items():
            if wf_node.type == "agent":
                try:
                    agent_data = schema.NodeDataAgent(**wf_node.data)
                except ValidationError as e:
                    raise ValueError(f"Invalid data for agent node '{wf_node.id}': {e.errors()}")

                agent_tools = []
                for edge in self.edges:
                    if edge.target == wf_node.id:
                        source_node = self.nodes_map.get(edge.source)
                        if source_node and source_node.type == "tool":
                            try:
                                tool_data = schema.NodeDataTool(**source_node.data)
                            except ValidationError as e:
                                raise ValueError(f"Invalid data for tool node '{source_node.id}': {e.errors()}")

                            try:
                                tool_instance = get_tool_instance(tool_data.tool_id, tool_data.config_params)
                                agent_tools.append(tool_instance)
                            except Exception as e:
                                raise ValueError(
                                    f"Failed to instantiate tool '{tool_data.tool_id}' for agent '{agent_data.name}': {e}")

                agent = Agent(
                    role=agent_data.role,
                    goal=agent_data.goal,
                    backstory=agent_data.backstory,
                    verbose=agent_data.verbose,
                    allow_delegation=agent_data.allow_delegation,
                    tools=agent_tools,
                    llm=self.llm
                )
                self.crew_agents.append(agent)
                self.agent_node_to_instance_map[wf_node.id] = agent

        if not self.crew_agents:
            raise ValueError("No agents defined in the workflow.")

    def _instantiate_tasks_and_map_agents(self) -> Dict[str, Dict[str, Any]]:
        task_configs: Dict[str, Dict[str, Any]] = {}

        for node_id, wf_node in self.nodes_map.items():
            if wf_node.type == "task":
                try:
                    task_data = schema.NodeDataTask(**wf_node.data)
                except ValidationError as e:
                    raise ValueError(f"Invalid data for task node '{wf_node.id}': {e.errors()}")

                assigned_agent_node_id: Optional[str] = None
                context_task_node_ids: List[str] = []

                for edge in self.edges:
                    if edge.target == wf_node.id:
                        source_node = self.nodes_map.get(edge.source)
                        if source_node:
                            if source_node.type == "agent":
                                assigned_agent_node_id = source_node.id
                            elif source_node.type == "task":
                                context_task_node_ids.append(source_node.id)

                if not assigned_agent_node_id:
                    raise ValueError(f"Task '{task_data.name}' (Node ID: {wf_node.id}) is not connected to an agent.")

                agent_instance = self.agent_node_to_instance_map.get(assigned_agent_node_id)
                if not agent_instance:
                    raise ValueError(
                        f"Agent for node ID '{assigned_agent_node_id}' (for task '{task_data.name}') not found.")

                task_configs[wf_node.id] = {
                    "description": task_data.description,
                    "expected_output": task_data.expected_output,
                    "agent_instance": agent_instance,
                    "context_task_node_ids": context_task_node_ids,
                }

        # Create Task instances (without context first)
        for ui_node_id, config in task_configs.items():
            task = Task(
                description=config["description"],
                expected_output=config["expected_output"],
                agent=config["agent_instance"]
            )
            self.task_node_to_instance_map[ui_node_id] = task

        return task_configs

    def _resolve_task_dependencies_and_order(self, task_configs: Dict[str, Dict[str, Any]]):
        for ui_node_id, task_instance in self.task_node_to_instance_map.items():
            config = task_configs[ui_node_id]
            context_instances = [
                self.task_node_to_instance_map[ctx_id]
                for ctx_id in config["context_task_node_ids"]
                if ctx_id in self.task_node_to_instance_map
            ]
            task_instance.context = context_instances

        # Topological sort (Kahn's algorithm)
        prerequisites: Dict[str, Set[str]] = {
            tid: set(task_configs[tid]["context_task_node_ids"])
            for tid in self.task_node_to_instance_map.keys()
        }

        in_degree: Dict[str, int] = {tid: 0 for tid in self.task_node_to_instance_map.keys()}
        adj: Dict[str, List[str]] = {tid: [] for tid in self.task_node_to_instance_map.keys()}

        for task_id, prereqs in prerequisites.items():
            in_degree[task_id] = len(prereqs)
            for prereq_id in prereqs:
                if prereq_id in adj:
                    adj[prereq_id].append(task_id)
                else:
                    print(
                        f"Warning: Prerequisite ID '{prereq_id}' for task '{task_id}' not found in adjacency list keys.")

        queue = [tid for tid, degree in in_degree.items() if degree == 0]

        while queue:
            task_id_to_add = queue.pop(0)
            self.ordered_crew_tasks.append(self.task_node_to_instance_map[task_id_to_add])

            for dependent_task_id in adj.get(task_id_to_add, []):
                in_degree[dependent_task_id] -= 1
                if in_degree[dependent_task_id] == 0:
                    queue.append(dependent_task_id)

        if len(self.ordered_crew_tasks) != len(self.task_node_to_instance_map):
            raise ValueError("Workflow has a cycle in task dependencies or invalid task structure.")

        if not self.ordered_crew_tasks and self.crew_agents:
            raise ValueError("No tasks could be prepared for the crew, but agents are present.")

    def _create_and_kickoff_crew(self) -> Any:
        if not self.ordered_crew_tasks:
            if self.crew_agents:  # Agents exist but no tasks
                return "Workflow has agents but no tasks to execute."
            else:  # No agents, no tasks
                return "Workflow is empty (no agents or tasks)."

        crew = Crew(
            agents=self.crew_agents,
            tasks=self.ordered_crew_tasks,
            process=Process.sequential,
            verbose=False
        )
        crew.verbose = 2

        result = crew.kickoff() # todo: blocking call, team should decide
        return result

    def build_and_run(self) -> Any:
        self._instantiate_agents_with_tools()
        raw_task_configs = self._instantiate_tasks_and_map_agents()
        if not self.task_node_to_instance_map:  # No tasks were created
            if self.crew_agents:
                return "Workflow has agents but no tasks defined or processed."
            return "Workflow is empty or has no executable tasks."
        self._resolve_task_dependencies_and_order(raw_task_configs)
        return self._create_and_kickoff_crew()
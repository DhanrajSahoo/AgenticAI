from crewai import Agent
from crew_agent.utils import rnd_id
from crew_agent.db_utils import save_agent, delete_agent
from crew_agent.llms import llm_providers_and_models, create_llm
from datetime import datetime

class MyAgent:
    def __init__(self, id=None, role=None, backstory=None, goal=None,
                 temperature=0.1, allow_delegation=False, verbose=True, cache=True,
                 llm_provider_model=None, max_iter=25, created_at=None, tools=None,
                 knowledge_source_ids=None, user_email=None):
        self.id = id or "A_" + rnd_id()
        self.role = role
        self.backstory = backstory or "Driven by curiosity..."
        self.goal = goal or "Uncover groundbreaking technologies in AI"
        self.temperature = temperature
        self.allow_delegation = allow_delegation
        self.verbose = verbose
        self.cache = cache
        self.llm_provider_model = llm_provider_model or llm_providers_and_models()[0]
        self.max_iter = max_iter
        self.created_at = created_at or datetime.now().isoformat()
        self.tools = tools or []
        self.knowledge_source_ids = knowledge_source_ids or []
        self.user_email = user_email or ''

    def get_crewai_agent(self, knowledge_sources_lookup: dict = None) -> Agent:
        llm = create_llm(self.llm_provider_model, temperature=self.temperature)
        tools = [tool.create_tool() for tool in self.tools]

        knowledge_sources = []
        if knowledge_sources_lookup and self.knowledge_source_ids:
            for ks_id in self.knowledge_source_ids:
                ks = knowledge_sources_lookup.get(ks_id)
                if ks:
                    try:
                        knowledge_sources.append(ks.get_crewai_knowledge_source())
                    except Exception as e:
                        print(f"Error loading knowledge source {ks_id}: {str(e)}")

        return Agent(
            role=self.role,
            backstory=self.backstory,
            goal=self.goal,
            allow_delegation=self.allow_delegation,
            verbose=self.verbose,
            max_iter=self.max_iter,
            cache=self.cache,
            tools=tools,
            llm=llm,
            knowledge_sources=knowledge_sources or None
        )

    def delete(self):
        delete_agent(self.id)

    def get_tool_display_name(self, tool):
        first_param_name = tool.get_parameter_names()[0] if tool.get_parameter_names() else None
        first_param_value = tool.parameters.get(first_param_name, '') if first_param_name else ''
        return f"{tool.name} ({first_param_value if first_param_value else tool.tool_id})"

    def is_valid(self):
        invalid_tools = []
        for tool in self.tools:
            if not tool.is_valid():
                invalid_tools.append(tool.name)
        if invalid_tools:
            return False, f"Invalid tools: {', '.join(invalid_tools)}"
        return True, "All tools are valid"

    def validate_llm_provider_model(self):
        available_models = llm_providers_and_models()
        if self.llm_provider_model not in available_models:
            self.llm_provider_model = available_models[0]


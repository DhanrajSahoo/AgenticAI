# db_utils.py
import os
import json
from crew_agent.my_tools import TOOL_CLASSES
from django.db import transaction
from django.utils.timezone import now
from crew_agent.my_knowledge_source import MyKnowledgeSource
from crew_agent.my_task import MyTask
from crew_agent.my_crew import MyCrew
from crew_agent.result import Result
from crew_agent.models import Entity


def save_entity(entity_type, entity_id, data):
    Entity.objects.update_or_create(
        id=entity_id,
        defaults={
            'entity_type': entity_type,
            'data': data
        }
    )

def load_entities(entity_type):
    rows = Entity.objects.filter(entity_type=entity_type)
    return [(row.id, row.data) for row in rows]

def delete_entity(entity_type, entity_id):
    Entity.objects.filter(id=entity_id, entity_type=entity_type).delete()

def save_tools_state(enabled_tools):
    save_entity('tools_state', 'enabled_tools', {'enabled_tools': enabled_tools})

def load_tools_state():
    rows = load_entities('tools_state')
    if rows:
        return rows[0][1].get('enabled_tools', {})
    return {}

def save_knowledge_source(knowledge_source):
    data = {
        'name': knowledge_source.name,
        'source_type': knowledge_source.source_type,
        'source_path': knowledge_source.source_path,
        'content': knowledge_source.content,
        'metadata': knowledge_source.metadata,
        'chunk_size': knowledge_source.chunk_size,
        'chunk_overlap': knowledge_source.chunk_overlap,
        'created_at': knowledge_source.created_at
    }
    save_entity('knowledge_source', knowledge_source.id, data)

def load_knowledge_sources():
    rows = load_entities('knowledge_source')
    return [MyKnowledgeSource(id=row[0], **row[1]) for row in rows]

def delete_knowledge_source(knowledge_source_id):
    delete_entity('knowledge_source', knowledge_source_id)

def save_agent(agent):
    data = {
        'created_at': agent.created_at,
        'role': agent.role,
        'backstory': agent.backstory,
        'goal': agent.goal,
        'allow_delegation': agent.allow_delegation,
        'verbose': agent.verbose,
        'cache': agent.cache,
        'llm_provider_model': agent.llm_provider_model,
        'temperature': agent.temperature,
        'max_iter': agent.max_iter,
        'tool_ids': [tool.tool_id for tool in agent.tools],
        'knowledge_source_ids': agent.knowledge_source_ids,
        'user_email':agent.user_email
    }
    save_entity('agent', agent.id, data)

def load_agents():
    from crew_agent.my_agent import MyAgent
    tools_dict = {tool.tool_id: tool for tool in load_tools()}
    rows = load_entities('agent')
    agents = []
    for row in rows:
        data = row[1]
        tool_ids = data.pop('tool_ids', [])
        agent = MyAgent(id=row[0], **data)
        agent.tools = [tools_dict[tool_id] for tool_id in tool_ids if tool_id in tools_dict]
        agents.append(agent)
    return agents

def delete_agent(agent_id):
    delete_entity('agent', agent_id)

def save_task(task):
    data = {
        'description': task.description,
        'expected_output': task.expected_output,
        'async_execution': task.async_execution,
        'agent_id': task.agent.id if task.agent else None,
        'context_from_async_tasks_ids': task.context_from_async_tasks_ids,
        'context_from_sync_tasks_ids': task.context_from_sync_tasks_ids,
        'created_at': task.created_at
    }
    save_entity('task', task.id, data)

def load_tasks():
    agents_dict = {agent.id: agent for agent in load_agents()}
    rows = load_entities('task')
    tasks = []
    for row in rows:
        data = row[1]
        agent_id = data.pop('agent_id', None)
        task = MyTask(id=row[0], agent=agents_dict.get(agent_id), **data)
        tasks.append(task)
    return tasks

def delete_task(task_id):
    delete_entity('task', task_id)

def save_crew(crew):
    data = {
        'name': crew.name,
        'process': crew.process,
        'verbose': crew.verbose,
        'agent_ids': [agent.id for agent in crew.agents],
        'task_ids': [task.id for task in crew.tasks],
        'memory': crew.memory,
        'cache': crew.cache,
        'planning': crew.planning,
        'max_rpm': crew.max_rpm,
        'manager_llm': crew.manager_llm,
        'manager_agent_id': crew.manager_agent.id if crew.manager_agent else None,
        'created_at': crew.created_at,
        'knowledge_source_ids': crew.knowledge_source_ids
    }
    save_entity('crew', crew.id, data)

def load_crews():
    agents_dict = {agent.id: agent for agent in load_agents()}
    tasks_dict = {task.id: task for task in load_tasks()}
    rows = load_entities('crew')
    crews = []
    for row in rows:
        data = row[1]
        crew = MyCrew(
            id=row[0],
            name=data['name'],
            process=data['process'],
            verbose=data['verbose'],
            created_at=data['created_at'],
            memory=data.get('memory'),
            cache=data.get('cache'),
            planning=data.get('planning'),
            max_rpm=data.get('max_rpm'),
            manager_llm=data.get('manager_llm'),
            manager_agent=agents_dict.get(data.get('manager_agent_id')),
            knowledge_source_ids=data.get('knowledge_source_ids', [])
        )
        crew.agents = [agents_dict[aid] for aid in data['agent_ids'] if aid in agents_dict]
        crew.tasks = [tasks_dict[tid] for tid in data['task_ids'] if tid in tasks_dict]
        crews.append(crew)
    return crews

def delete_crew(crew_id):
    delete_entity('crew', crew_id)

def save_tool(tool):
    data = {
        'name': tool.name,
        'description': tool.description,
        'parameters': tool.get_parameters()
    }
    save_entity('tool', tool.tool_id, data)

def load_tools():
    rows = load_entities('tool')
    tools = []
    for row in rows:
        data = row[1]
        tool_class = TOOL_CLASSES[data['name']]
        tool = tool_class(tool_id=row[0])
        tool.set_parameters(**data['parameters'])
        tools.append(tool)
    return tools

def delete_tool(tool_id):
    delete_entity('tool', tool_id)

def export_to_json(file_path):
    rows = Entity.objects.all().values('id', 'entity_type', 'data')
    with open(file_path, 'w') as f:
        json.dump(list(rows), f, indent=4)

def import_from_json(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)

    with transaction.atomic():
        for entity in data:
            save_entity(entity['entity_type'], entity['id'], entity['data'])

def save_result(result):
    data = {
        'crew_id': result.crew_id,
        'crew_name': result.crew_name,
        'inputs': result.inputs,
        'result': result.result,
        'created_at': result.created_at
    }
    save_entity('result', result.id, data)

def load_results():
    rows = load_entities('result')
    return [Result(id=row[0], **row[1]) for row in rows]

def delete_result(result_id):
    delete_entity('result', result_id)

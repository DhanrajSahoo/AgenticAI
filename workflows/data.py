workflow_data = {
    "name": "Test",
    "nodes": [
    {
      "id": "0",
      "type": "custom",
      "data": {
        "label": "Agent"
      },
      "position": {
        "x": 200,
        "y": 50
      },
      "zIndex": 1000,
      "measured": {
        "width": 185,
        "height": 272
      },
      "selected": False,
      "meta": {
        "agent_name": "Agent 1",
        "agent_model": "deepseek-r1",
        "agent_goal": "goal 1",
        "agent_backstory": "back story 1"
      },
      "source": None,
      "target": [
        "1"
      ]
    },
    {
      "id": "1",
      "type": "custom",
      "data": {
        "label": "Task"
      },
      "position": {
        "x": 450,
        "y": 50
      },
      "zIndex": 1000,
      "measured": {
        "width": 185,
        "height": 110
      },
      "selected": False,
      "meta": {
        "agent_name": "",
        "agent_model": "",
        "agent_goal": "",
        "agent_backstory": "",
        "task": "task-1"
      },
      "source": [
        "0"
      ],
      "target": [
        "2"
      ]
    },
    {
      "id": "2",
      "type": "custom",
      "data": {
        "label": "Agent"
      },
      "position": {
        "x": 700,
        "y": 50
      },
      "zIndex": 1000,
      "measured": {
        "width": 185,
        "height": 272
      },
      "selected": True,
      "meta": {
        "agent_name": "Agent 2",
        "agent_model": "llama3",
        "agent_goal": "goal 2",
        "agent_backstory": "back story 2"
      },
      "source": [
        "1"
      ],
      "target": None
    }
  ]
}


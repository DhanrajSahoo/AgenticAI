from crewai_tools.tools.tavily_search_tool.tavily_search_tool import TavilySearchTool
import json
import json
import os
from typing import Type

from pydantic import BaseModel, Field

from crewai.tools import BaseTool
os.environ["TAVILY_API_KEY"] = "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"


class TavilyQuerySchema(BaseModel):
  query: str = Field(..., description="What you want to know")

  class Config:
    allow_population_by_field_name = True
    allow_population_by_alias = True


class TavilyQueryTool(BaseTool):
  name: str = "Tavily Search Tool"
  description: str = "Runs a professional/personal detail search via Tavily"
  args_schema: Type[TavilyQuerySchema] = TavilyQuerySchema


  def _run(self, query: str) -> str:
    try:
      client = TavilySearchTool(api_key='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', max_results=10,
                                description='Need all professional and personal details')
      raw = client._run(query)  # returns a JSON string
      data = json.loads(raw)
      results = data.get("results", [])
      if not results:
        return "No results found."

      out = []
      for idx, item in enumerate(results, start=1):
        out.append(
          f"Result {idx}:\n"
          f"URL: {item.get('url')}\n"
          f"Content: {item.get('content')}\n"
        )
      return "\n".join(out)

    except Exception as e:
      return f"Search failed: {e}"

  def run(self, input_data: TavilyQuerySchema) -> str:
    return self._run(input_data.query)
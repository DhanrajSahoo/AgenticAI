import os
import json
from typing import Type
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
import requests
from dotenv import load_dotenv
import logging
load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Step 1: Schema for input
class SerperQuerySchema(BaseModel):
    search_query: str = Field(..., description="Mandatory search query you want to use to search the internet")

    class Config:
        allow_population_by_field_name = True
        allow_population_by_alias = True


# Step 2: Custom tool using Serper API
class SerperQueryTool(BaseTool):
    name: str = "Serper Search Tool"
    description: str = "Runs a Google search using Serper API and returns summarized search results"
    args_schema: Type[SerperQuerySchema] = SerperQuerySchema

    def _run(self, search_query: str) -> str:
        try:
            logger.info("Inside serper")
            api_key = os.getenv("SERPER_API_KEY") 
            if not api_key:
                return "SERPER_API_KEY not set in environment."

            url = "https://google.serper.dev/search"
            headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
            payload = {"q": search_query}

            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()

            data = response.json()
            results = data.get("organic", [])

            if not results:
                return "No results found."

            out = []
            for idx, item in enumerate(results[:5], start=1):
                out.append(
                    f"Result {idx}:\n"
                    f"Title: {item.get('title')}\n"
                    f"Link: {item.get('link')}\n"
                    f"Snippet: {item.get('snippet')}\n"
                )
            return "\n".join(out)

        except Exception as e:
            return f"Search failed: {e}"

    def run(self, input_data: SerperQuerySchema) -> str:
        return self._run(input_data.search_query)

# if __name__ == "__main__":
#     tool = SerperQueryTool()
#     query = "find 7 best places in the world for hiking"
#     query_schema = SerperQuerySchema(search_query=query)
#     result = tool.run(input_data=query_schema)
#     print(result)

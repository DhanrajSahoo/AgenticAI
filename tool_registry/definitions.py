from crewai_tools import SerperDevTool, ScrapeWebsiteTool, GithubSearchTool # Example

PREDEFINED_TOOLS_CONFIG = {
    "serper_dev_tool": {
        "name": "Serper Search",
        "description": "Tool for performing Google searches via Serper API. Requires SERPER_API_KEY environment variable.",
        "class": SerperDevTool,
        "parameters_schema": None
    },
    "website_scraper": {
        "name": "Website Scraper",
        "description": "Tool to scrape content from a website. The agent provides the URL during task execution, or it can be pre-configured.",
        "class": ScrapeWebsiteTool,
        "parameters_schema": {
            "website_url": {
                "type": "text",
                "label": "Website URL (Optional)",
                "required": False,
                "description": "If provided, the tool will always use this URL. Otherwise, agent must provide it."
            }
        }
    },
    "github_search_tool": {
        "name": "GitHub Search Tool",
        "description": "Searches GitHub repositories, issues, pull requests, etc. Requires GITHUB_TOKEN for higher rate limits (optional).",
        "class": GithubSearchTool,
        "parameters_schema": {
            "github_repo": {
                "type": "text",
                "label": "GitHub Repository (e.g., owner/repo)",
                "required": False,
                "description": "Specific repository to search within. If not set, searches all GitHub."
            },
            "gh_token": {
                "type": "text",
                "label": "GitHub Token (Optional, from env recommended)",
                "required": False,
                "description": "GitHub personal access token. Recommended to set GITHUB_TOKEN environment variable instead."
            },
            "content_types": {
                "type": "text",
                "label": "Content Types (e.g., code,issues)",
                "required": False,
                "default": "code,issues,pr",
                "description": "Comma-separated list of content types to search (code, issues, pr, users, etc.)."

            }
        }
    }
}
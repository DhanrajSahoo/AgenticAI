from crewai_tools import SerperDevTool, ScrapeWebsiteTool, GithubSearchTool # Example
from tool_registry.tools.AudioRecorder import VoiceRecorderTool
from tool_registry.tools.EmailSenderTool import EmailSenderTool
from tool_registry.tools.EvaluateSummarization import EvaluateSummaryTool
from tool_registry.tools.TranscribeAudioTool import TranscribeAudioTool

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
                "label": "Website URL",
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
                "label": "Repository (owner/repo)",
                "required": False,
                "description": "Specific repository to search within. If not set, searches all GitHub."
            },
            "gh_token": {
                "type": "text",
                "label": "GitHub Token",
                "required": False,
                "description": "Personal access token. Recommended to set GITHUB_TOKEN environment variable instead."
            },
            "content_types": {
                "type": "text",
                "label": "Content Types",
                "required": False,
                "default": "code,issues,pr",
                "description": "Comma-separated list of content types to search (code, issues, pr, users, etc.)."
            }
        }
    },
    "audio_recorder_tool": {
        "name": "Audio Record",
        "description": "Tool for recording the audio.",
        "class": VoiceRecorderTool,
        "parameters_schema": {
            "duration": {
                "type": "number",
                "label": "Duration (seconds)",
                "required": True,
                "description": "Duration of recording in seconds."
            }
        }
    },
    "email_sender": {
        "name": "Email Sender",
        "description": "Tool for sending emails.",
        "class": EmailSenderTool,
        "parameters_schema": {
            "recipient": {
                "type": "text",
                "label": "Recipient Email",
                "required": True,
                "description": "Email address of the recipient."
            },
            "subject": {
                "type": "text",
                "label": "Subject",
                "required": True,
                "description": "Email subject line."
            },
            "body": {
                "type": "text",
                "label": "Body",
                "required": True,
                "description": "Plain text email body content."
            }
        }
    },
    "evaluate_summarize": {
        "name": "Evaluate Summarization",
        "description": "Tool for evaluating a generated summary against a transcript.",
        "class": EvaluateSummaryTool,
        "parameters_schema": {
            "transcript": {
                "type": "text",
                "label": "Transcript",
                "required": True,
                "description": "Original transcript text to compare against."
            },
            "summary": {
                "type": "text",
                "label": "Summary",
                "required": True,
                "description": "Generated summary to evaluate."
            }
        }
    },
    "transcribe_audio": {
        "name": "Transcribe Audio",
        "description": "Tool for transcribing audio to text.",
        "class": TranscribeAudioTool,
        "parameters_schema": {
            "audio_file_path": {
                "type": "text",
                "label": "Audio File Path",
                "required": True,
                "description": "Full path to the audio file (e.g., audio/meeting1.mp3)."
            }
        }
    }
}

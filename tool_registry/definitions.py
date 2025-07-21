from crewai_tools import SerperDevTool, ScrapeWebsiteTool, GithubSearchTool
from tool_registry.tools.AudioRecorder import VoiceRecorderTool
from tool_registry.tools.EmailSenderTool import EmailSenderTool
from tool_registry.tools.EvaluateSummarization import EvaluateSummaryTool
from tool_registry.tools.TranscribeAudioTool import TranscribeAudioTool
from tool_registry.tools.Pdfsearchtool import PDFQueryTool
from tool_registry.tools.WordSearchTool import DocQueryTool
from tool_registry.tools.CsvSearchTool import CsvQueryTool
from tool_registry.tools.RagTool import RAGQueryTool
from tool_registry.tools.Fileparser import FILEReaderTool
from tool_registry.tools.TavilyTool import TavilyQueryTool


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
        }
    },

    # Custom Tools
    "VoiceRecorderTool": { 
        "name": "Voice Recorder", 
        "description": "Tool for recording audio from the microphone.",
        "class": VoiceRecorderTool,
        "parameters_schema": {
            "duration": {
                "type": "number",
                "label": "Duration (seconds)",
                "required": True,
                "description": "Duration of recording in seconds. Agent must provide this."
            }
        }
    },
    "EmailSenderTool": { 
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
                "type": "textarea",
                "label": "Body",
                "required": True,
                "description": "Plain text email body content."
            }
        }
    },
    "EvaluateSummaryTool": { 
        "name": "Evaluate Summarization", 
        "description": "Tool for evaluating a generated summary against a transcript.",
        "class": EvaluateSummaryTool,
        "parameters_schema": {
            "transcript": {
                "type": "textarea", 
                "label": "Transcript",
                "required": True,
                "description": "Original transcript text to compare against."
            },
            "summary": {
                "type": "textarea", 
                "label": "Summary",
                "required": True,
                "description": "Generated summary to evaluate."
            }
        }
    },
    "TranscribeAudioTool": { 
        "name": "Transcribe Audio", 
        "description": "Tool for transcribing audio to text using OpenAI Whisper.",
        "class": TranscribeAudioTool,
        "parameters_schema": {
            "file_path": {
                "type": "text",
                "label": "Audio File Path",
                "required": True,
                "description": "Full path to the audio file (e.g., /path/to/audio/meeting1.mp3). Agent must provide this."
            },
            "upload_button": {
                "type": "fileupload",
                "label": "Upload-Button",
                "required": True,
                "description": "Button to upload the audion file"
            }
        }
    },
    "PdfSearchTool": {
        "name": "PdfSearchTool",
        "description": "Tool for extracting relevant text from doc.",
        "class": PDFQueryTool,
        "parameters_schema": {
            "file_path": {
                "type": "text",
                "label": "pdf File Path",
                "required": True,
                "description": "Full path to the pdf file (e.g., /path/to/audio/document.pdf). Agent must provide this."
            },
            "prompt": {
                "type": "text",
                "label": "question",
                "required": True,
                "description": "query to perform search in pdf file"
            },
            "upload_button": {
                "type": "fileupload",
                "label": "Upload-Button",
                "required": True,
                "description": "Button to upload the audion file"
            }
        }
    },
    "WordSearchTool": {
        "name": "WordSearchTool",
        "description": "Tool for extracting relevant text from doc",
        "class": DocQueryTool,
        "parameters_schema": {
            "file_path": {
                "type": "text",
                "label": "word File Path",
                "required": True,
                "description": "Full path to the word file (e.g., /path/to/audio/document.docx). Agent must provide this."
            },
            "prompt": {
                "type": "text",
                "label": "question",
                "required": True,
                "description": "query to perform search in word file"
            },
            "upload_button": {
                "type": "fileupload",
                "label": "Upload-Button",
                "required": True,
                "description": "Button to upload the audion file"
            }
        }
    },
    "CsvSearchTool": {
        "name": "CsvSearchTool",
        "description": "Tool for extracting relevant text from CSV data frame",
        "class": CsvQueryTool,
        "parameters_schema": {
            "file_path": {
                "type": "text",
                "label": "csv File Path",
                "required": True,
                "description": "Full path to the csv file (e.g., /path/to/audio/document.csv). Agent must provide this."
            },
            "prompt": {
                "type": "text",
                "label": "question",
                "required": True,
                "description": "query to perform search in csv file"
            },
            "upload_button": {
                "type": "fileupload",
                "label": "Upload-Button",
                "required": True,
                "description": "Button to upload the audion file"
            }
        }
    },
    "RagTool": {
        "name": "RagTool",
        "description": "Tool for extracting relevant text from all type of files",
        "class": RAGQueryTool,
        "parameters_schema": {
            # "filename": {
            #     "type": "text",
            #     "label": "filename",
            #     "required": True,
            #     "description": "File name to get the similar text"
            # },
            "prompt": {
                "type": "text",
                "label": "question",
                "required": True,
                "description": "query to perform search in csv file"
            },
            "upload_button": {
                "type": "fileupload",
                "label": "Upload-Button",
                "required": True,
                "description": "Button to upload the file"
            },
            "uploaded_file": {
                "type": "select",
                "label": "Select File",
                "required": True,
                "default": None,
                "description": "List of all available file",
                "options": None,
                "accept": None
            }
        }
    },
    "FILEReaderTool": {
        "name": "FILEReaderTool",
        "description": "Tool for extracting relevant text from doc.",
        "class": FILEReaderTool,
        "parameters_schema": {
            "file_path": {
                "type": "text",
                "label": "pdf File Path",
                "required": True,
                "description": "Full path to the pdf file (e.g., /path/to/audio/document.pdf). Agent must provide this."
            },
            "upload_button": {
                "type": "fileupload",
                "label": "Upload-Button",
                "required": True,
                "description": "Button to upload the audion file"
            }
        }
    },
    "TavilyTool": {
        "name": "Tavily Search Tool",
        "description": "Runs a professional/personal detail search via Tavily",
        "class": TavilyQueryTool,
        "parameters_schema": {
            "query": {
                "type": "text",
                "label": "Query",
                "required": True,
                "description": "what you want to know about a person"
            }
        }
    }
    
}
#!/usr/bin/env python3
"""
GitLab MCP Server - Model Context Protocol server for GitLab API integration
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types
from gitlab_api import GitLabClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gitlab-mcp-server")

# Create the MCP server instance
app = Server("gitlab-mcp")


@app.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available GitLab tools"""
    return [
        types.Tool(
            name="gitlab_get_project",
            description="Get GitLab project details",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="gitlab_list_merge_requests",
            description="List merge requests for a GitLab project",
            inputSchema={
                "type": "object",
                "properties": {
                    "state": {
                        "type": "string",
                        "description": "State of MRs (opened, closed, merged, all)",
                        "default": "opened"
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="gitlab_get_merge_request",
            description="Get details of a specific merge request",
            inputSchema={
                "type": "object",
                "properties": {
                    "mr_iid": {
                        "type": "integer",
                        "description": "Merge request IID"
                    }
                },
                "required": ["mr_iid"]
            }
        ),
        types.Tool(
            name="gitlab_create_merge_request",
            description="Create a new merge request",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_branch": {
                        "type": "string",
                        "description": "Source branch name"
                    },
                    "target_branch": {
                        "type": "string",
                        "description": "Target branch name"
                    },
                    "title": {
                        "type": "string",
                        "description": "MR title"
                    },
                    "description": {
                        "type": "string",
                        "description": "MR description"
                    }
                },
                "required": ["source_branch", "target_branch", "title"]
            }
        ),
        types.Tool(
            name="gitlab_list_pipelines",
            description="List pipelines for a GitLab project",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter by status"
                    },
                    "ref": {
                        "type": "string",
                        "description": "Filter by ref/branch"
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="gitlab_get_pipeline",
            description="Get details of a specific pipeline",
            inputSchema={
                "type": "object",
                "properties": {
                    "pipeline_id": {
                        "type": "integer",
                        "description": "Pipeline ID"
                    }
                },
                "required": ["pipeline_id"]
            }
        ),
        types.Tool(
            name="gitlab_list_jobs",
            description="List jobs for a project or pipeline",
            inputSchema={
                "type": "object",
                "properties": {
                    "pipeline_id": {
                        "type": "integer",
                        "description": "Optional pipeline ID"
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="gitlab_get_job_log",
            description="Get the log of a specific job",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "integer",
                        "description": "Job ID"
                    }
                },
                "required": ["job_id"]
            }
        ),
        types.Tool(
            name="gitlab_list_branches",
            description="List branches for a GitLab project",
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {
                        "type": "string",
                        "description": "Search term for branches"
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="gitlab_get_file",
            description="Get file content from GitLab repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file"
                    },
                    "ref": {
                        "type": "string",
                        "description": "Branch/tag/commit ref",
                        "default": "main"
                    }
                },
                "required": ["file_path"]
            }
        ),
        types.Tool(
            name="gitlab_list_commits",
            description="List commits for a GitLab project",
            inputSchema={
                "type": "object",
                "properties": {
                    "ref_name": {
                        "type": "string",
                        "description": "Branch/tag name"
                    },
                    "since": {
                        "type": "string",
                        "description": "ISO 8601 date string"
                    },
                    "until": {
                        "type": "string",
                        "description": "ISO 8601 date string"
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="gitlab_get_merge_request_changes",
            description="Get the changes (diffs) for a specific merge request",
            inputSchema={
                "type": "object",
                "properties": {
                    "mr_iid": {
                        "type": "integer",
                        "description": "Merge request IID"
                    }
                },
                "required": ["mr_iid"]
            }
        ),
        # Enhanced search tools
        types.Tool(
            name="gitlab_search_files",
            description="Search for files matching glob patterns (like find/ls)",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Glob pattern (e.g., '**/*.py', '*test*')"
                    },
                    "ref": {
                        "type": "string",
                        "description": "Branch/tag/commit ref",
                        "default": "main"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum files to return",
                        "default": 100
                    }
                },
                "required": ["pattern"]
            }
        ),
        types.Tool(
            name="gitlab_grep_content",
            description="Search file contents for patterns (like grep -r)",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Regex pattern to search for"
                    },
                    "file_filter": {
                        "type": "string",
                        "description": "File pattern filter (e.g., '*.py')"
                    },
                    "ref": {
                        "type": "string",
                        "description": "Branch/tag/commit ref",
                        "default": "main"
                    },
                    "case_insensitive": {
                        "type": "boolean",
                        "description": "Case insensitive search",
                        "default": False
                    },
                    "context_lines": {
                        "type": "integer",
                        "description": "Lines of context around matches",
                        "default": 0
                    }
                },
                "required": ["pattern"]
            }
        ),
        types.Tool(
            name="gitlab_search_commits",
            description="Search commits with advanced filtering (like git log --grep)",
            inputSchema={
                "type": "object",
                "properties": {
                    "grep": {
                        "type": "string",
                        "description": "Search commit messages (regex supported)"
                    },
                    "author": {
                        "type": "string",
                        "description": "Filter by author name/email"
                    },
                    "since": {
                        "type": "string",
                        "description": "ISO 8601 date string"
                    },
                    "until": {
                        "type": "string",
                        "description": "ISO 8601 date string"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum commits to return",
                        "default": 20
                    }
                }
            }
        ),
        # MR action tools
        types.Tool(
            name="gitlab_approve_merge_request",
            description="Approve a merge request",
            inputSchema={
                "type": "object",
                "properties": {
                    "mr_iid": {
                        "type": "integer",
                        "description": "Merge request IID"
                    }
                },
                "required": ["mr_iid"]
            }
        ),
        types.Tool(
            name="gitlab_merge_merge_request",
            description="Merge a merge request",
            inputSchema={
                "type": "object",
                "properties": {
                    "mr_iid": {
                        "type": "integer",
                        "description": "Merge request IID"
                    },
                    "merge_commit_message": {
                        "type": "string",
                        "description": "Custom merge commit message"
                    },
                    "should_remove_source_branch": {
                        "type": "boolean",
                        "description": "Remove source branch after merge",
                        "default": True
                    }
                },
                "required": ["mr_iid"]
            }
        ),
        types.Tool(
            name="gitlab_add_merge_request_note",
            description="Add a comment to a merge request",
            inputSchema={
                "type": "object",
                "properties": {
                    "mr_iid": {
                        "type": "integer",
                        "description": "Merge request IID"
                    },
                    "body": {
                        "type": "string",
                        "description": "Comment text"
                    }
                },
                "required": ["mr_iid", "body"]
            }
        )
    ]


@app.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls for GitLab operations"""
    client = GitLabClient()

    try:
        if name == "gitlab_get_project":
            result = await client.get_project()

        elif name == "gitlab_list_merge_requests":
            result = await client.list_merge_requests(
                arguments.get("state", "opened")
            )

        elif name == "gitlab_get_merge_request":
            result = await client.get_merge_request(
                client.project_id,
                arguments["mr_iid"]
            )

        elif name == "gitlab_create_merge_request":
            result = await client.create_merge_request(
                client.project_id,
                arguments["source_branch"],
                arguments["target_branch"],
                arguments["title"],
                arguments.get("description")
            )

        elif name == "gitlab_list_pipelines":
            result = await client.list_pipelines(
                client.project_id,
                arguments.get("status"),
                arguments.get("ref")
            )

        elif name == "gitlab_get_pipeline":
            result = await client.get_pipeline(
                client.project_id,
                arguments["pipeline_id"]
            )

        elif name == "gitlab_list_jobs":
            result = await client.list_jobs(
                client.project_id,
                arguments.get("pipeline_id")
            )

        elif name == "gitlab_get_job_log":
            result = await client.get_job_log(
                client.project_id,
                arguments["job_id"]
            )

        elif name == "gitlab_list_branches":
            result = await client.list_branches(
                client.project_id,
                arguments.get("search")
            )

        elif name == "gitlab_get_file":
            result = await client.get_file(
                client.project_id,
                arguments["file_path"],
                arguments.get("ref", "main")
            )

        elif name == "gitlab_list_commits":
            result = await client.list_commits(
                client.project_id,
                arguments.get("ref_name"),
                arguments.get("since"),
                arguments.get("until")
            )

        elif name == "gitlab_get_merge_request_changes":
            result = await client.get_merge_request_changes(
                client.project_id,
                arguments["mr_iid"]
            )

        # Enhanced search tools
        elif name == "gitlab_search_files":
            result = await client.search_files(
                client.project_id,
                arguments["pattern"],
                arguments.get("ref", "main"),
                arguments.get("max_results", 100)
            )

        elif name == "gitlab_grep_content":
            result = await client.grep_repository_content(
                client.project_id,
                arguments["pattern"],
                arguments.get("file_filter"),
                arguments.get("ref", "main"),
                arguments.get("case_insensitive", False),
                arguments.get("context_lines", 0)
            )

        elif name == "gitlab_search_commits":
            result = await client.search_commits_enhanced(
                client.project_id,
                arguments.get("grep"),
                arguments.get("author"),
                arguments.get("file_path"),
                arguments.get("since"),
                arguments.get("until"),
                arguments.get("limit", 20)
            )

        # MR action tools
        elif name == "gitlab_approve_merge_request":
            result = await client.approve_merge_request(
                client.project_id,
                arguments["mr_iid"]
            )

        elif name == "gitlab_merge_merge_request":
            result = await client.merge_merge_request(
                client.project_id,
                arguments["mr_iid"],
                arguments.get("merge_commit_message"),
                arguments.get("should_remove_source_branch", True)
            )

        elif name == "gitlab_add_merge_request_note":
            result = await client.add_merge_request_note(
                client.project_id,
                arguments["mr_iid"],
                arguments["body"]
            )

        else:
            return [types.TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]

        # Format the result
        if isinstance(result, str):
            return [types.TextContent(type="text", text=result)]
        else:
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]

    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


async def main():
    """Main entry point for the MCP server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="gitlab-mcp",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
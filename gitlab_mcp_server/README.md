# GitLab MCP Server

A Model Context Protocol (MCP) server for GitLab API integration with Claude Code.

## Features

- Project management
- Merge request operations
- Pipeline and job monitoring
- Branch and file operations
- Commit history

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure GitLab credentials

The server reads configuration from `.claude/.gitlab-config`. Create this file with:

```bash
GITLAB_TOKEN=your_gitlab_token
GITLAB_URL=https://your.gitlab.instance
PROJECT_ID=default_project_id
PROJECT_NAME=Project Name
PROJECT_PATH=group/project-path
```

### 3. Add to Claude Code configuration

Add this server to your Claude Code MCP settings file (`~/AppData/Roaming/Claude/config.json` on Windows or `~/.config/claude/config.json` on Linux/Mac):

```json
{
  "mcpServers": {
    "gitlab": {
      "command": "python",
      "args": ["/path/to/gitlab_mcp_server/server.py"],
      "cwd": "/path/to/gitlab_mcp_server"
    }
  }
}
```

Or if you prefer using uvx (recommended):

```json
{
  "mcpServers": {
    "gitlab": {
      "command": "uvx",
      "args": ["--from", "/path/to/gitlab_mcp_server", "gitlab-mcp"],
      "env": {
        "GITLAB_TOKEN": "your_token_here",
        "GITLAB_URL": "https://your.gitlab.instance"
      }
    }
  }
}
```

## Available Tools

- `gitlab_get_project` - Get project details
- `gitlab_list_merge_requests` - List MRs
- `gitlab_get_merge_request` - Get specific MR
- `gitlab_get_merge_request_changes` - Get MR changes/diffs
- `gitlab_create_merge_request` - Create new MR
- `gitlab_list_pipelines` - List pipelines
- `gitlab_get_pipeline` - Get pipeline details
- `gitlab_list_jobs` - List jobs
- `gitlab_get_job_log` - Get job logs
- `gitlab_list_branches` - List branches
- `gitlab_get_file` - Get file content
- `gitlab_list_commits` - List commits

## Testing

Run the test client:

```bash
python test_gitlab.py
```

## Notes

- Uses curl-based approach with SSL bypass (-k flag) for internal GitLab instances
- Supports retry logic for network reliability
- Configuration is loaded from `.claude/.gitlab-config`
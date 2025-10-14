# Leveraging MCP to Improve Your Workflows

## Introduction

Model Context Protocol (MCP) is a powerful extensibility framework that allows Claude Code to integrate with external tools, APIs, and services. By implementing custom MCP servers, you can dramatically expand Claude Code's capabilities beyond its built-in features, enabling seamless integration with your development infrastructure, CI/CD pipelines, project management tools, and more.

This section demonstrates real-world MCP implementation through a comprehensive GitLab integration example, showing you how to build custom MCP servers, create specialized workflow commands, and orchestrate multiple agents for complex development tasks.

**What You'll Learn:**
- Understanding MCP architecture and how it extends Claude Code
- Building custom MCP servers from scratch
- Creating workflow automation with custom slash commands
- Orchestrating specialized review agents in parallel
- Implementing secure configuration management
- Designing production-ready MCP integrations

## Understanding Model Context Protocol (MCP)

### What is MCP?

Model Context Protocol is Claude Code's standardized interface for connecting AI assistants with external data sources and tools. Think of it as a plugin system that allows Claude Code to:

- **Access external APIs** (GitLab, GitHub, Jira, etc.)
- **Interact with databases** (query project data, metrics, logs)
- **Control CI/CD systems** (trigger pipelines, monitor builds)
- **Integrate with development tools** (IDEs, testing frameworks, deployment platforms)
- **Read external documentation** (company wikis, API docs, runbooks)

### How MCP Works with Claude Code

```
┌─────────────────────────────────────────────────────────┐
│                     Claude Code                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Main Conversation Thread                  │  │
│  │  - User prompts                                   │  │
│  │  - Claude responses                               │  │
│  │  - Tool execution requests                        │  │
│  └────────────────┬─────────────────────────────────┘  │
│                   │                                      │
│  ┌────────────────▼─────────────────────────────────┐  │
│  │          MCP Client Layer                         │  │
│  │  - Discovers available MCP servers                │  │
│  │  - Routes tool calls to appropriate servers       │  │
│  │  - Manages server lifecycle                       │  │
│  └────────────────┬─────────────────────────────────┘  │
└───────────────────┼──────────────────────────────────────┘
                    │
        ┌───────────┴───────────┬─────────────┐
        │                       │             │
┌───────▼────────┐     ┌───────▼────────┐   ▼
│ GitLab MCP     │     │ GitHub MCP     │  ...
│ Server         │     │ Server         │
│                │     │                │
│ - 17+ tools    │     │ - PR reviews   │
│ - MR reviews   │     │ - Issue mgmt   │
│ - Pipelines    │     │ - Workflows    │
└────────────────┘     └────────────────┘
```

### MCP Architecture Components

1. **MCP Server** - Python/Node.js process that exposes tools via stdin/stdout
2. **Tool Definitions** - JSON schemas describing available operations
3. **Tool Handlers** - Functions that execute when tools are called
4. **Configuration** - Claude Code settings that register MCP servers

## MCP Integration and Workflow Enhancement

### Real-World Example: GitLab MCP Integration

This guide includes a complete, production-ready GitLab MCP implementation that demonstrates:

- **Custom MCP Server**: Full-featured GitLab API integration with 17+ tools
- **Automated Setup**: `/gitlab-setup` command for zero-friction configuration
- **Intelligent MR Reviews**: `/mr-review_gitlab` command with parallel agent orchestration
- **Specialized Agents**: Three focused review agents for code quality, documentation, and README updates
- **Security Best Practices**: Secure credential management and gitignore integration

### GitLab MCP Server Overview

The custom GitLab MCP server (`gitlab_mcp_server/`) provides comprehensive GitLab integration:

**Available Tools (17+):**
- **Project Management**: `gitlab_get_project`
- **Merge Requests**: `gitlab_list_merge_requests`, `gitlab_get_merge_request`, `gitlab_get_merge_request_changes`, `gitlab_create_merge_request`, `gitlab_approve_merge_request`, `gitlab_merge_merge_request`, `gitlab_add_merge_request_note`
- **Pipelines**: `gitlab_list_pipelines`, `gitlab_get_pipeline`
- **Jobs**: `gitlab_list_jobs`, `gitlab_get_job_log`
- **Repository**: `gitlab_list_branches`, `gitlab_get_file`, `gitlab_list_commits`
- **Search**: `gitlab_search_files`, `gitlab_grep_content`, `gitlab_search_commits`

**Key Implementation Details:**
- Uses curl-based approach with SSL bypass for corporate networks
- Automatic retry logic for network reliability (3 attempts with 2s delay)
- Configuration loaded from `.claude/.gitlab-config`
- Handles encoding issues on Windows (UTF-8/latin-1 fallback)
- Base64 decoding for file content

### Setting Up GitLab MCP Integration

#### Step 1: Install the MCP Server

```bash
# Navigate to your project
cd your-project/

# Install dependencies
cd gitlab_mcp_server/
pip install -r requirements.txt
```

#### Step 2: Configure Claude Code MCP Settings

Add the GitLab MCP server to your Claude Code configuration file:

**Windows**: `%APPDATA%\Roaming\Claude\config.json`
**Linux/Mac**: `~/.config/claude/config.json`

```json
{
  "mcpServers": {
    "gitlab": {
      "command": "python",
      "args": ["/absolute/path/to/gitlab_mcp_server/server.py"],
      "cwd": "/absolute/path/to/gitlab_mcp_server"
    }
  }
}
```

**Alternative (using uvx - recommended):**
```json
{
  "mcpServers": {
    "gitlab": {
      "command": "uvx",
      "args": ["--from", "/absolute/path/to/gitlab_mcp_server", "gitlab-mcp"],
      "env": {
        "GITLAB_TOKEN": "your_token_here",
        "GITLAB_URL": "https://your.gitlab.instance"
      }
    }
  }
}
```

#### Step 3: Configure GitLab Credentials Using `/gitlab-setup`

The `/gitlab-setup` command automates GitLab API configuration:

```bash
# Auto-detect from git remote and configure
/gitlab-setup --token <your-gitlab-token>

# Custom GitLab instance
/gitlab-setup --token <token> --url https://gitlab.company.com

# Save globally for all projects
/gitlab-setup --token <token> --global

# Test existing configuration
/gitlab-setup --test
```

**What `/gitlab-setup` does:**
1. Parses token and URL arguments
2. Auto-detects GitLab URL from `git remote get-url origin`
3. Tests API connectivity with retry logic
4. **Auto-detects Project ID using exact path matching** (not just name)
5. Validates project access
6. Generates `.claude/.gitlab-config` with all settings
7. Configures Git remote with token authentication
8. Sets secure permissions (600) on config file
9. Adds config to `.gitignore`

**Generated Configuration File** (`.claude/.gitlab-config`):
```bash
# GitLab API Configuration for project-name
# Auto-generated by /gitlab-setup command
GITLAB_TOKEN=your-gitlab-token-here
GITLAB_URL=https://gitlab.company.com
PROJECT_ID=12345
PROJECT_NAME=my-project
PROJECT_PATH=group/my-project
# Created: 2025-01-15 10:30:00
```

#### Critical Setup Considerations

**Project ID Detection:**
- Uses **exact path matching** instead of name search to avoid wrong project selection
- Falls back to search with path validation if direct access fails
- Example: Distinguishes "cosmote-testing-lovable-ui" from "cosmote-testing"

**Network Reliability:**
- Implements 3-attempt retry logic for API calls
- Uses 10s connect timeout, 20s max timeout
- Bypasses SSL verification with `-k` flag for corporate networks

### Automated Merge Request Review Workflow

The `/mr-review_gitlab` command provides comprehensive MR review using GitLab MCP tools and specialized agents.

#### Review Workflow Architecture

```
User: /mr-review_gitlab 123
         │
         ▼
┌─────────────────────────────────────────────────┐
│ 1. Parse Arguments & Create Todo List           │
└───────────────┬─────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────┐
│ 2. Get MR Info Using MCP Tools                  │
│    - gitlab_get_merge_request (MR details)      │
│    - gitlab_get_merge_request_changes (diffs)   │
│    - Extract source/target branches             │
└───────────────┬─────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────┐
│ 3. Analyze Changed Files                        │
│    - Use gitlab_get_file for content            │
│    - Focus only on changed files                │
└───────────────┬─────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────┐
│ 4. Load Requirements from .claude/.mr-requirements.md │
└───────────────┬─────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────┐
│ 5. Launch Specialized Agents in PARALLEL        │
│    ┌─────────────────────────────────────────┐ │
│    │ Agent 1: code-quality-reviewer          │ │
│    │  - Coding standards                     │ │
│    │  - Print statements                     │ │
│    │  - TODO comments                        │ │
│    │  - Code structure                       │ │
│    └─────────────────────────────────────────┘ │
│    ┌─────────────────────────────────────────┐ │
│    │ Agent 2: documentation-reviewer         │ │
│    │  - Function/class docstrings           │ │
│    │  - Parameter documentation             │ │
│    │  - Return value docs                   │ │
│    └─────────────────────────────────────────┘ │
│    ┌─────────────────────────────────────────┐ │
│    │ Agent 3: readme-reviewer                │ │
│    │  - README update requirements          │ │
│    │  - CHANGELOG needs                     │ │
│    │  - Project documentation               │ │
│    └─────────────────────────────────────────┘ │
│    ┌─────────────────────────────────────────┐ │
│    │ Manual Checks (main thread)             │ │
│    │  - Commit message format               │ │
│    │  - Branch naming                       │ │
│    │  - Security issues                     │ │
│    └─────────────────────────────────────────┘ │
└───────────────┬─────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────┐
│ 6. Synthesize Results from All Agents           │
│    - Collect findings from 3 agents             │
│    - Combine with manual checks                 │
└───────────────┬─────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────┐
│ 7. Generate Unified Review Report               │
│    - Overall PASS/FAIL status                   │
│    - Agent-specific findings                    │
│    - Aggregated issues by priority             │
│    - Specific file:line references             │
│    - Actionable recommendations                │
└───────────────┬─────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────┐
│ 8. Interactive Actions                          │
│    - Approve MR (if --approve flag)             │
│    - Add comment (if --comment flag)            │
│    - Merge MR (if --merge flag)                 │
└─────────────────────────────────────────────────┘
```

#### Using the Review Command

**Basic Usage:**
```bash
# Review merge request !123
/mr-review_gitlab 123

# Review with specific branches
/mr-review_gitlab 123 --source feature/auth --target main

# Custom requirements file
/mr-review_gitlab 123 --config .claude/custom-requirements.md

# Review and approve
/mr-review_gitlab 123 --approve

# Review, approve, and merge
/mr-review_gitlab 123 --approve --merge

# Add review as MR comment
/mr-review_gitlab 123 --comment

# Verbose output
/mr-review_gitlab 123 --verbose

# Only list changed files (no review)
/mr-review_gitlab 123 --files-only
```

#### Specialized Review Agents

**1. Code Quality Reviewer** (`.claude/agents/code-quality-reviewer.md`)

**Focus Areas:**
- Code structure and best practices
- Function/class design and complexity
- DRY violations
- Error handling patterns
- Production code issues (print statements, debug code, TODO comments)
- Coding standards (naming, formatting, line length)
- Performance concerns

**Scoring Criteria:**
- No CRITICAL issues: minimum 60%
- No HIGH issues: minimum 80%
- Only LOW issues: 90-100%

**Output Format:**
```
Issue: [CRITICAL] Print statement in production code
File: auth/login.py:45
Description: Debug print statement found in login function
Suggested Fix: Replace with proper logging: logger.info(...)
Category: Debug Code
```

**2. Documentation Reviewer** (`.claude/agents/documentation-reviewer.md`)

**Focus Areas:**
- Function docstrings for ALL public functions
- Parameter descriptions with types
- Return value documentation
- Exception documentation
- Class-level docstrings
- Module-level documentation
- Usage examples for complex functions

**Scoring Criteria:**
- 100%: All public entities documented with high quality
- 90%+: All public entities documented, minor quality issues
- 80%+: Most entities documented, some missing params/returns
- 60%+: Basic documentation present, significant gaps
- <60%: Major documentation missing

**Output Format:**
```
Missing Documentation [CRITICAL]
- auth/utils.py:validate_token (line 23) - No docstring
- auth/utils.py:refresh_session (line 67) - Missing parameter docs

Inadequate Documentation [HIGH]
- auth/login.py:authenticate (line 12) - Unclear return value description

Documentation Quality Score: 75%
Rating: Needs Improvement
```

**3. README Reviewer** (`.claude/agents/readme-reviewer.md`)

**Focus Areas:**
- New features requiring documentation
- Installation/setup changes (new dependencies)
- Configuration changes (env vars, config files)
- Breaking changes to public APIs
- New CLI commands or scripts
- Project structure changes

**Scoring Criteria:**
- README update required: New public APIs, dependencies, configuration, breaking changes
- README update NOT required: Internal refactoring, bug fixes, test changes, private methods

**Output Format:**
```
README Impact Assessment
- Change Type: New Feature
- User Impact: HIGH
- README Update Needed: YES

Specific Sections to Update:
1. Installation - Add new dependency: redis-py
2. Configuration - Document REDIS_URL environment variable
3. Usage Examples - Add example for new cache management API
```

### Parallel Agent Execution Strategy

The MR review workflow launches three specialized agents **simultaneously** using Claude Code's `Task` tool:

```python
# Conceptual parallel execution
Task(subagent_type="code-quality-reviewer",
     prompt="Review code quality for MR !123...")

Task(subagent_type="documentation-reviewer",
     prompt="Review documentation for MR !123...")

Task(subagent_type="readme-reviewer",
     prompt="Review README needs for MR !123...")

# All three execute in parallel, results synthesized when complete
```

**Benefits of Parallel Execution:**
- **Speed**: 3x faster than sequential reviews
- **Specialization**: Each agent focuses on its domain expertise
- **Clarity**: Clean separation of concerns
- **Scalability**: Easy to add new review dimensions

### MCP Tools in Action

The review workflow leverages these MCP tools:

```bash
# Get MR basic details
mcp__gitlab__gitlab_get_merge_request(mr_iid=123)
# Returns: title, description, author, status, source_branch, target_branch

# Get file changes and diffs
mcp__gitlab__gitlab_get_merge_request_changes(mr_iid=123)
# Returns: array of changed files with diffs, additions, deletions

# Get file content from specific branch
mcp__gitlab__gitlab_get_file(file_path="auth/login.py", ref="feature/auth")
# Returns: base64-decoded file content

# Get project details (for permissions check)
mcp__gitlab__gitlab_get_project()
# Returns: project info, user access level (for approve/merge permissions)

# Approve MR (if user has permissions)
mcp__gitlab__gitlab_approve_merge_request(mr_iid=123)

# Add review comment
mcp__gitlab__gitlab_add_merge_request_note(mr_iid=123, body="Review results...")

# Merge MR
mcp__gitlab__gitlab_merge_merge_request(mr_iid=123, should_remove_source_branch=true)
```

### Configuration Management

**Configuration Priority:**
1. **Project-specific**: `.claude/.gitlab-config` (highest priority)
2. **Global**: `~/.claude/gitlab-config`
3. **Environment**: `$GITLAB_TOKEN`, `$GITLAB_URL`

**Security Best Practices:**
- Config files automatically added to `.gitignore`
- Permissions set to 600 (owner read/write only)
- Tokens never logged or displayed in output
- Git remote configured with token auth (not stored in plaintext in git config)

### Workflow Integration with Other Claude Code Features

**Integration with Slash Commands:**
```bash
# Custom slash commands can use MCP tools
/gitlab-setup --token $TOKEN     # Sets up MCP integration
/mr-review_gitlab 123            # Uses MCP tools + subagents
```

**Integration with Subagents:**
```bash
# Subagents can access MCP tools defined in their `tools:` metadata
# Example from documentation-reviewer.md:
---
tools: Read, Grep, Glob, mcp__gitlab__gitlab_get_file, mcp__gitlab__gitlab_get_merge_request_changes
---
```

**Integration with TODO List Tracking:**
```bash
# Review workflow creates and updates TODO list
- [in_progress] Get MR information from GitLab API
- [in_progress] Launch specialized review agents
- [pending] Synthesize results from all agents
- [pending] Generate unified review report
```

### Extending the GitLab MCP Server

The custom MCP server is designed for extensibility. Here's how to add new tools:

**1. Define Tool in `server.py`:**
```python
types.Tool(
    name="gitlab_get_pipeline_status",
    description="Get pipeline status for a merge request",
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
)
```

**2. Implement Handler in `gitlab_api.py`:**
```python
async def get_pipeline_status(self, project_id: str, mr_iid: int) -> Dict:
    """Get pipeline status for MR"""
    # Get MR details first
    mr = await self.get_merge_request(project_id, mr_iid)
    pipeline_id = mr.get("head_pipeline", {}).get("id")

    if pipeline_id:
        return await self.get_pipeline(project_id, pipeline_id)
    return {"status": "no_pipeline"}
```

**3. Add Tool Handler in `server.py`:**
```python
elif name == "gitlab_get_pipeline_status":
    result = await client.get_pipeline_status(
        client.project_id,
        arguments["mr_iid"]
    )
```

### Creating Your Own MCP Servers

**Project Structure:**
```
your-mcp-server/
├── server.py              # Main MCP server entry point
├── api_client.py          # API/service integration
├── requirements.txt       # Python dependencies
├── README.md             # Setup and usage instructions
└── package.json          # npm metadata (optional)
```

**Minimal MCP Server Template:**
```python
#!/usr/bin/env python3
import asyncio
from mcp.server import Server
import mcp.server.stdio
import mcp.types as types

app = Server("your-server-name")

@app.list_tools()
async def handle_list_tools():
    return [
        types.Tool(
            name="your_tool_name",
            description="What your tool does",
            inputSchema={
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "Parameter description"
                    }
                },
                "required": ["param1"]
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name == "your_tool_name":
        # Implement tool logic
        result = f"Processed: {arguments['param1']}"
        return [types.TextContent(type="text", text=result)]

async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, ...)

if __name__ == "__main__":
    asyncio.run(main())
```

### MCP Use Cases Beyond GitLab

**Development Infrastructure:**
- **GitHub Integration**: PR reviews, issue management, workflow automation
- **Jira/Linear**: Ticket creation, sprint planning, status updates
- **Slack/Teams**: Notifications, channel queries, message posting
- **Jenkins/CircleCI**: Build triggers, log analysis, deployment tracking

**Data Access:**
- **Databases**: Query project metrics, user data, analytics
- **Elasticsearch**: Log searching, error aggregation, monitoring
- **Metrics Systems**: Datadog, Prometheus queries
- **Documentation**: Confluence, Notion, internal wikis

**Cloud Services:**
- **AWS**: EC2 management, S3 operations, Lambda deployments
- **Azure**: Resource management, deployments
- **GCP**: Cloud functions, storage operations
- **Docker/Kubernetes**: Container management, deployment status

## Best Practices for MCP Integration

### 1. Security and Credentials Management
- **Never commit credentials** - Always use `.gitignore` for config files
- **Use environment variables** for sensitive data when possible
- **Set restrictive permissions** (600) on config files
- **Rotate tokens regularly** and document rotation procedures
- **Validate token permissions** during setup

### 2. Error Handling and Reliability
- **Implement retry logic** for network operations (3 attempts minimum)
- **Use appropriate timeouts** (10s connect, 20s max)
- **Handle encoding issues** gracefully (UTF-8/latin-1 fallback)
- **Provide meaningful error messages** with troubleshooting steps
- **Log errors** without exposing sensitive data

### 3. Tool Design Principles
- **Single responsibility** - Each tool does one thing well
- **Clear descriptions** - Tool purposes must be immediately obvious
- **Strong typing** - Use JSON schemas with required fields
- **Consistent naming** - Follow `service_action_resource` pattern (e.g., `gitlab_get_merge_request`)
- **Idempotency** - Tools should be safe to call multiple times

### 4. Performance Optimization
- **Batch operations** when possible (list operations)
- **Cache expensive queries** (project metadata, user info)
- **Limit result sets** with pagination (default to 20-100 items)
- **Use selective filters** to reduce data transfer
- **Implement streaming** for large responses (logs, diffs)

### 5. Workflow Design
- **Compose complex workflows** from simple tools
- **Use parallel execution** for independent operations
- **Create specialized agents** for focused review dimensions
- **Track progress** with TODO lists
- **Provide interactive options** after automated tasks

### 6. Testing and Validation
- **Test tool definitions** with JSON schema validators
- **Create test scripts** that exercise all tools (e.g., `test_gitlab.py`)
- **Validate API connectivity** during setup
- **Test error scenarios** (network failures, invalid tokens, missing projects)
- **Document troubleshooting steps** for common issues

### 7. Documentation Standards
- **README with setup instructions** - Clear, step-by-step guidance
- **Tool descriptions** - What each tool does, parameters, return values
- **Configuration examples** - Show all configuration options
- **Workflow examples** - End-to-end usage scenarios
- **Troubleshooting guide** - Common issues and solutions

## Advanced MCP Patterns

### Pattern 1: Multi-Stage Workflows
Break complex tasks into stages with checkpoints:
```
Stage 1: Setup & Validation → Stage 2: Data Gathering →
Stage 3: Parallel Processing → Stage 4: Synthesis →
Stage 5: Interactive Actions
```

### Pattern 2: Conditional Tool Execution
Use MCP tools to gather information, then decide which tools to call next:
```python
# Get MR details first
mr_info = gitlab_get_merge_request(123)

# Conditionally check pipelines if MR has CI
if mr_info.has_pipeline:
    pipeline_status = gitlab_get_pipeline(mr_info.pipeline_id)
```

### Pattern 3: Agent Orchestration
Coordinate multiple specialized agents with different tool access:
```
Agent A (read-only): Analysis and reporting
Agent B (write): Making changes based on Agent A findings
Agent C (reviewer): Validating Agent B changes
```

### Pattern 4: Progressive Enhancement
Start with basic MCP integration, progressively add capabilities:
```
v1: Read-only tools (get, list)
v2: Write tools (create, update)
v3: Advanced search and filtering
v4: Automated workflows and agents
v5: Interactive actions and approvals
```

## Troubleshooting Common MCP Issues

### MCP Server Not Detected
**Problem**: Claude Code doesn't show MCP tools
**Solutions**:
1. Verify `config.json` syntax (valid JSON)
2. Check absolute paths in `command` and `args`
3. Restart Claude Code after config changes
4. Test server manually: `python server.py` (should wait for input)

### Authentication Failures
**Problem**: "401 Unauthorized" errors
**Solutions**:
1. Verify token has correct permissions (api, read_repository, write_repository)
2. Check token expiration date in GitLab
3. Test token with curl: `curl -k -H "Authorization: Bearer $TOKEN" $URL/api/v4/user`
4. Ensure `.gitlab-config` is being read (check permissions)

### Project ID Detection Issues
**Problem**: Wrong project or "Project not found"
**Solutions**:
1. Use exact path matching (not name search)
2. Verify `git remote get-url origin` output
3. Manually specify project ID in config
4. Check project visibility (private vs public)
5. Verify token has access to the project

### Network Connectivity Problems
**Problem**: Timeouts or "HTTP 000" responses
**Solutions**:
1. Increase timeout values (20s → 30s)
2. Add more retry attempts (3 → 5)
3. Check corporate proxy settings
4. Verify SSL bypass with `-k` flag
5. Test network: `curl -k $GITLAB_URL`

### Tool Execution Errors
**Problem**: Tools fail during execution
**Solutions**:
1. Check tool input parameters match schema
2. Verify API endpoint availability
3. Review server logs for detailed errors
4. Test API endpoint manually with curl
5. Check rate limiting (GitLab: 600 requests/minute)

## References to Official Documentation

### Official Claude Code Documentation
- **MCP Overview**: [Model Context Protocol Introduction](https://docs.anthropic.com/en/docs/model-context-protocol/introduction)
- **Building MCP Servers**: [Creating MCP Servers Guide](https://docs.anthropic.com/en/docs/model-context-protocol/building-servers)
- **MCP Configuration**: [Configuring MCP in Claude Code](https://docs.anthropic.com/en/docs/claude-code/mcp-integration)
- **Tool Design Best Practices**: [MCP Tool Development Guidelines](https://docs.anthropic.com/en/docs/model-context-protocol/tools)
- **Security Considerations**: [MCP Security Best Practices](https://docs.anthropic.com/en/docs/model-context-protocol/security)

### Related Claude Code Features
- **Slash Commands**: See Section 11 - Slash Commands
- **Subagents**: See Section 12 - Subagents
- **Tool Usage Control**: See Section 5 - Tool Usage (allow, deny)
- **Context Window Management**: See Section 6 - Context Window Management

### External Resources
- **GitLab API Documentation**: [GitLab REST API](https://docs.gitlab.com/ee/api/)
- **MCP Specification**: [Model Context Protocol Spec](https://github.com/anthropics/model-context-protocol)
- **Python MCP SDK**: [mcp PyPI Package](https://pypi.org/project/mcp/)

### Example Implementations
This section's examples demonstrate real-world MCP integration:
- `examples/gitlab-mcp-setup-workflow.md` - Complete setup walkthrough
- `examples/mr-review-workflow.md` - End-to-end MR review process
- `examples/custom-mcp-server.md` - Building your own MCP server
- `examples/parallel-agent-execution.md` - Orchestrating specialized agents

For best practices and common mistakes, see:
- `DOS.md` - MCP development and workflow best practices

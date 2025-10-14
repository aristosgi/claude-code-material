# MCP Development and Workflow Best Practices

This document outlines best practices for developing Model Context Protocol (MCP) servers and designing effective MCP-powered workflows in Claude Code.

## MCP Server Development

### Architecture and Design

**DO design tools with single responsibility**
```python
# ✅ GOOD - Each tool does one thing
gitlab_get_merge_request()      # Get MR details
gitlab_get_merge_request_changes()  # Get MR diffs
gitlab_approve_merge_request()   # Approve MR

# ❌ BAD - Tool tries to do too much
gitlab_manage_merge_request(action="get|approve|merge|comment")
```

**DO use clear, descriptive tool names following a consistent pattern**
- Pattern: `service_action_resource`
- Examples: `gitlab_get_merge_request`, `github_create_pull_request`, `jira_update_ticket`
- Makes tools immediately discoverable and understandable

**DO provide comprehensive tool descriptions**
```python
types.Tool(
    name="gitlab_get_merge_request_changes",
    description="Get the file changes and diffs for a specific merge request. Returns array of changed files with additions, deletions, and diff content. Use this to analyze what code changed in an MR.",
    inputSchema={...}
)
```

**DO use strong typing with JSON schemas**
```python
# ✅ GOOD - Clear types, required fields, descriptions
{
    "type": "object",
    "properties": {
        "mr_iid": {
            "type": "integer",
            "description": "Merge request IID (internal ID, not global ID)"
        },
        "include_diffs": {
            "type": "boolean",
            "description": "Include full diff content",
            "default": True
        }
    },
    "required": ["mr_iid"]
}
```

**DO design idempotent tools**
- Tools should be safe to call multiple times with same inputs
- GET operations are naturally idempotent
- POST/PUT operations should handle duplicates gracefully
- Example: Creating a comment twice should not create duplicate comments

**DO organize tools into logical groups**
```
Project Management: get_project, list_projects
Merge Requests: list_mrs, get_mr, create_mr, approve_mr, merge_mr
Pipelines: list_pipelines, get_pipeline, trigger_pipeline
Repository: get_file, list_branches, list_commits
```

### Error Handling and Reliability

**DO implement comprehensive retry logic**
```python
async def _make_request(self, endpoint: str, retries: int = 3):
    for attempt in range(1, retries + 1):
        try:
            result = await self._execute_request(endpoint)
            if result.success:
                return result

            if attempt < retries:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        except NetworkError as e:
            logger.warning(f"Attempt {attempt} failed: {e}")
            if attempt == retries:
                raise
```

**DO use appropriate timeouts**
- Connect timeout: 10s (time to establish connection)
- Max timeout: 20-30s (total request time)
- Adjust based on endpoint characteristics (file operations may need longer)

**DO handle encoding issues gracefully**
```python
# Corporate networks and Windows can cause encoding issues
try:
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
except UnicodeDecodeError:
    # Fallback to binary mode with manual decoding
    result = subprocess.run(cmd, capture_output=True)
    stdout = result.stdout.decode('utf-8', errors='replace')
```

**DO provide meaningful error messages with context**
```python
# ✅ GOOD - Actionable error messages
raise Exception(
    f"Failed to get merge request !{mr_iid}. "
    f"Possible causes: "
    f"1. MR does not exist in project {project_id} "
    f"2. Insufficient permissions (need Developer role) "
    f"3. Token expired or invalid. "
    f"Check: /gitlab-setup --test"
)

# ❌ BAD - Vague error
raise Exception("API call failed")
```

**DO log errors without exposing sensitive data**
```python
# ✅ GOOD - Sanitized logging
logger.error(f"Authentication failed for URL: {self.base_url}/api/v4/...")

# ❌ BAD - Token exposed in logs
logger.error(f"Auth failed with token: {self.token}")
```

### Security Best Practices

**DO use secure configuration management**
```python
# Configuration priority (highest to lowest):
# 1. Project-specific: .claude/.gitlab-config
# 2. Global: ~/.claude/gitlab-config
# 3. Environment variables: GITLAB_TOKEN, GITLAB_URL

def _load_config(self):
    # Try project config first
    if os.path.exists(".claude/.gitlab-config"):
        return self._parse_config(".claude/.gitlab-config")
    # Fall back to global
    elif os.path.exists(os.path.expanduser("~/.claude/gitlab-config")):
        return self._parse_config(os.path.expanduser("~/.claude/gitlab-config"))
    # Fall back to environment
    else:
        return {
            "GITLAB_TOKEN": os.getenv("GITLAB_TOKEN", ""),
            "GITLAB_URL": os.getenv("GITLAB_URL", "")
        }
```

**DO automatically add config files to .gitignore**
```python
# After generating config file
if os.path.exists(".gitignore"):
    with open(".gitignore", "a") as f:
        f.write("\n# GitLab MCP configuration\n")
        f.write(".claude/.gitlab-config\n")
```

**DO set restrictive permissions on config files**
```python
import os
import stat

# Set permissions to 600 (owner read/write only)
os.chmod(".claude/.gitlab-config", stat.S_IRUSR | stat.S_IWUSR)
```

**DO validate token permissions during setup**
```python
# Test token and get user info
async def validate_token(self):
    try:
        user_info = await self._make_request("/api/v4/user")
        logger.info(f"Authenticated as: {user_info['username']}")

        # Check token scopes
        required_scopes = ["api", "read_repository"]
        # GitLab API v4 doesn't expose scopes directly, but we can test access
        await self._make_request(f"/api/v4/projects/{project_id}")

        return True
    except Exception as e:
        raise Exception(f"Token validation failed: {e}")
```

**DO never log, display, or transmit tokens in plaintext**
```python
# ✅ GOOD - Token masked in output
print(f"Configuration saved with token: {token[:4]}...{token[-4:]}")

# ❌ BAD - Full token displayed
print(f"Token: {token}")
```

### Performance Optimization

**DO implement caching for expensive queries**
```python
from functools import lru_cache
import time

class GitLabClient:
    def __init__(self):
        self._project_cache = {}
        self._cache_ttl = 300  # 5 minutes

    async def get_project(self, project_id: str):
        cache_key = project_id
        cached = self._project_cache.get(cache_key)

        if cached and (time.time() - cached['timestamp']) < self._cache_ttl:
            return cached['data']

        # Fetch from API
        data = await self._make_request(f"/api/v4/projects/{project_id}")
        self._project_cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }
        return data
```

**DO use pagination for list operations**
```python
async def list_merge_requests(self, state="opened", per_page=20, page=1):
    endpoint = f"/api/v4/projects/{self.project_id}/merge_requests"
    params = f"?state={state}&per_page={per_page}&page={page}"
    return await self._make_request(endpoint + params)
```

**DO limit result sets by default**
```python
# Default to reasonable limits
async def search_files(self, pattern: str, max_results: int = 100):
    # Prevent returning thousands of files
    matching_files = []
    for item in tree:
        if fnmatch.fnmatch(item['path'], pattern):
            matching_files.append(item)
            if len(matching_files) >= max_results:
                break
    return matching_files
```

**DO batch operations when possible**
```python
# ✅ GOOD - Batch fetch files
async def get_multiple_files(self, file_paths: List[str], ref: str):
    tasks = [self.get_file(path, ref) for path in file_paths]
    return await asyncio.gather(*tasks)

# ❌ BAD - Sequential fetches
files = []
for path in file_paths:
    files.append(await self.get_file(path, ref))
```

### Testing and Validation

**DO create comprehensive test scripts**
```python
# test_gitlab.py
async def test_all_tools():
    client = GitLabClient()

    # Test project access
    print("Testing: gitlab_get_project...")
    project = await client.get_project()
    assert project['id'], "Project ID missing"

    # Test MR operations
    print("Testing: gitlab_list_merge_requests...")
    mrs = await client.list_merge_requests()
    assert isinstance(mrs, list), "MRs should be a list"

    # Test file operations
    print("Testing: gitlab_get_file...")
    file_content = await client.get_file("README.md", "main")
    assert 'content' in file_content, "File content missing"

    print("✅ All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_all_tools())
```

**DO validate API connectivity during setup**
```python
def test_api_connectivity(url: str, token: str):
    for i in range(1, 4):
        try:
            response = requests.get(
                f"{url}/api/v4/version",
                headers={"Authorization": f"Bearer {token}"},
                verify=False,  # -k flag equivalent
                timeout=10
            )
            if response.status_code == 200:
                version = response.json().get("version")
                print(f"✅ Connected to GitLab {version}")
                return True
        except Exception as e:
            print(f"⚠️ Attempt {i}/3 failed: {e}")
            time.sleep(2)

    print("❌ API connectivity test failed")
    return False
```

**DO test error scenarios**
- Invalid tokens (401 Unauthorized)
- Missing projects (404 Not Found)
- Network timeouts
- Malformed requests (400 Bad Request)
- Rate limiting (429 Too Many Requests)

### Documentation Standards

**DO provide clear README with step-by-step setup**
```markdown
# GitLab MCP Server

## Quick Start
1. Install dependencies: `pip install -r requirements.txt`
2. Configure Claude Code: Add to `config.json` (see below)
3. Set up credentials: `/gitlab-setup --token YOUR_TOKEN`
4. Test: `/gitlab-setup --test`

## Configuration
[Detailed configuration instructions...]

## Available Tools
[Complete list of tools with descriptions...]

## Troubleshooting
[Common issues and solutions...]
```

**DO document all tool parameters**
```python
types.Tool(
    name="gitlab_get_merge_request",
    description="Get details of a specific merge request",
    inputSchema={
        "type": "object",
        "properties": {
            "mr_iid": {
                "type": "integer",
                "description": "Merge request IID (internal ID visible in GitLab UI, e.g., !123)"
            }
        },
        "required": ["mr_iid"]
    }
)
```

**DO include configuration examples for all scenarios**
```json
// Basic configuration
{"mcpServers": {"gitlab": {"command": "python", "args": ["server.py"]}}}

// With environment variables
{"mcpServers": {"gitlab": {"command": "python", "args": ["server.py"], "env": {"GITLAB_TOKEN": "token"}}}}

// Using uvx
{"mcpServers": {"gitlab": {"command": "uvx", "args": ["--from", ".", "gitlab-mcp"]}}}
```

## MCP Workflow Design

### Workflow Architecture

**DO break complex workflows into stages**
```
Stage 1: Setup & Validation
  → Parse arguments
  → Validate prerequisites
  → Create TODO list

Stage 2: Data Gathering
  → Fetch required data via MCP tools
  → Extract relevant information

Stage 3: Parallel Processing
  → Launch specialized agents
  → Execute independent checks

Stage 4: Synthesis
  → Collect agent results
  → Combine findings
  → Generate unified report

Stage 5: Interactive Actions
  → Present results to user
  → Offer next steps (approve/merge/comment)
```

**DO use TODO lists to track workflow progress**
```python
# Create TODO list at workflow start
TodoWrite([
    {"content": "Get MR information from GitLab API", "status": "in_progress"},
    {"content": "Launch specialized review agents", "status": "pending"},
    {"content": "Synthesize results from all agents", "status": "pending"},
    {"content": "Generate unified review report", "status": "pending"}
])

# Update as you progress
TodoWrite([
    {"content": "Get MR information from GitLab API", "status": "completed"},
    {"content": "Launch specialized review agents", "status": "in_progress"},
    ...
])
```

**DO design workflows to be resumable**
- Save intermediate results
- Allow workflows to be paused and continued
- Store workflow state in config or temp files

**DO provide clear progress indicators**
```
📋 MR !123: Add authentication feature
🔀 feature/auth → main
👤 Author: John Doe

[1/5] Getting MR details... ✅
[2/5] Analyzing changed files... ✅
[3/5] Running specialized reviews... 🔄
  ├─ Code quality review... ✅
  ├─ Documentation review... ✅
  └─ README review... 🔄
[4/5] Synthesizing results... ⏳
[5/5] Generating report... ⏳
```

### Agent Orchestration

**DO use parallel execution for independent tasks**
```python
# Launch three agents in parallel (single message, multiple Task calls)
Task(subagent_type="code-quality-reviewer",
     description="Review code quality",
     prompt=f"Review code quality for MR !{mr_id}. Changed files: {files}")

Task(subagent_type="documentation-reviewer",
     description="Review documentation",
     prompt=f"Review documentation for MR !{mr_id}. Changed files: {files}")

Task(subagent_type="readme-reviewer",
     description="Check README updates",
     prompt=f"Check if README needs updates for MR !{mr_id}. Changes: {changes}")
```

**DO give agents focused responsibilities**
```markdown
# code-quality-reviewer agent
Focus ONLY on:
- Code structure and best practices
- Production code issues (print statements, TODOs)
- Coding standards

Do NOT review:
- Documentation (handled by documentation-reviewer)
- README (handled by readme-reviewer)
```

**DO define clear agent interfaces**
```yaml
---
name: documentation-reviewer
description: Reviews function/class docstrings for completeness
tools: Read, Grep, Glob, mcp__gitlab__gitlab_get_file
input: List of changed files
output: Documentation quality score + list of missing/inadequate docs
---
```

**DO synthesize agent results into unified output**
```python
# Collect results from all agents
code_quality_score = agent1_results['score']
documentation_score = agent2_results['score']
readme_needed = agent3_results['update_needed']

# Generate unified report
overall_score = (code_quality_score + documentation_score) / 2
overall_status = "PASS" if overall_score >= 80 and not readme_needed else "NEEDS WORK"

print(f"""
=== MR Review Summary ===
Overall Status: {overall_status}
Overall Score: {overall_score}/100

Code Quality: {code_quality_score}/100
  - {len(agent1_results['issues'])} issues found

Documentation: {documentation_score}/100
  - {agent2_results['missing_count']} functions undocumented

README Updates: {"REQUIRED" if readme_needed else "NOT NEEDED"}
""")
```

### Slash Command Design

**DO provide clear argument hints**
```yaml
---
argument-hint: [mr-id|HEAD] [--source branch] [--target branch] [--config file] [--approve] [--merge]
---
```

**DO support both required and optional arguments**
```bash
# Required argument
/mr-review_gitlab 123

# Optional flags
/mr-review_gitlab 123 --approve --merge

# Optional parameters
/mr-review_gitlab 123 --source feature/auth --target main
```

**DO implement intelligent defaults**
```python
# Default to current branch if not specified
source_branch = args.get('--source') or current_branch()

# Default to main/master if not specified
target_branch = args.get('--target') or detect_default_branch()

# Default config location
config_file = args.get('--config') or '.claude/.mr-requirements.md'
```

**DO provide helpful usage examples in command docs**
```markdown
## Examples

# Basic review
/mr-review_gitlab 123

# Review and approve
/mr-review_gitlab 123 --approve

# Custom config
/mr-review_gitlab 123 --config team-standards.md

# Verbose output
/mr-review_gitlab 123 --verbose
```

### Configuration Management

**DO use project-specific configs with global fallback**
```python
def load_config():
    # 1. Project-specific (highest priority)
    if os.path.exists(".claude/.gitlab-config"):
        return load_from_file(".claude/.gitlab-config")

    # 2. Global fallback
    global_config = os.path.expanduser("~/.claude/gitlab-config")
    if os.path.exists(global_config):
        return load_from_file(global_config)

    # 3. Environment variables (lowest priority)
    return {
        "GITLAB_TOKEN": os.getenv("GITLAB_TOKEN"),
        "GITLAB_URL": os.getenv("GITLAB_URL")
    }
```

**DO validate configuration on first use**
```python
def ensure_configured():
    config = load_config()

    if not config.get("GITLAB_TOKEN"):
        raise ConfigError(
            "GitLab not configured. Run: /gitlab-setup --token YOUR_TOKEN"
        )

    if not config.get("PROJECT_ID"):
        print("⚠️ PROJECT_ID not set. Running auto-detection...")
        detect_project_id()
```

**DO provide setup commands that validate configuration**
```bash
# Setup validates everything
/gitlab-setup --token TOKEN
  → Tests API connectivity
  → Validates project access
  → Generates complete config
  → Sets permissions
  → Updates .gitignore

# Test command re-validates
/gitlab-setup --test
  → Checks token validity
  → Confirms project access
  → Tests MCP tool availability
```

### Integration Patterns

**DO integrate MCP workflows with existing Claude Code features**

**With Tool Permissions:**
```yaml
---
allowed-tools: mcp__gitlab__*, Read, Bash(git *), Grep, TodoWrite, Task
---
```

**With Subagents:**
```yaml
---
name: code-reviewer
tools: Read, Grep, mcp__gitlab__gitlab_get_file, mcp__gitlab__gitlab_get_merge_request_changes
---
```

**With TODO Tracking:**
```python
# Workflow creates and maintains TODO list
TodoWrite([...])  # Initialize at start
TodoWrite([...])  # Update after each stage
TodoWrite([...])  # Mark complete at end
```

**With Context Management:**
```python
# Use MCP tools to minimize context usage
# Instead of reading entire files, use GitLab API to get only changed sections
changes = await gitlab_get_merge_request_changes(mr_id)
for file in changes['changes']:
    # Only process diff hunks, not entire files
    analyze_diff(file['diff'])
```

## Common Pitfalls to Avoid

### Project ID Detection

**DON'T use project name search alone**
```python
# ❌ BAD - May return wrong project
response = requests.get(f"{url}/api/v4/projects?search={project_name}")
project_id = response.json()[0]['id']  # First match might be wrong!

# ✅ GOOD - Use exact path matching
project_path = "group/subgroup/project-name"
encoded_path = urllib.parse.quote(project_path, safe='')
response = requests.get(f"{url}/api/v4/projects/{encoded_path}")
project_id = response.json()['id']
```

### Error Handling

**DON'T fail silently**
```python
# ❌ BAD - Error swallowed
try:
    result = await client.get_merge_request(mr_id)
except:
    pass  # What happened? User has no idea!

# ✅ GOOD - Informative error handling
try:
    result = await client.get_merge_request(mr_id)
except AuthenticationError:
    raise Exception("Token invalid or expired. Run: /gitlab-setup --token NEW_TOKEN")
except NotFoundError:
    raise Exception(f"MR !{mr_id} not found in project {project_id}")
except Exception as e:
    raise Exception(f"Failed to get MR !{mr_id}: {e}")
```

### Security

**DON'T commit configuration files**
```bash
# ✅ GOOD - Always in .gitignore
.claude/.gitlab-config
.claude/.github-config
*.secret
*.token
```

**DON'T expose tokens in logs or output**
```python
# ❌ BAD
logger.debug(f"Using token: {self.token}")
print(f"Config: {config}")  # Config contains token!

# ✅ GOOD
logger.debug("Token loaded successfully")
safe_config = {k: v for k, v in config.items() if 'token' not in k.lower()}
print(f"Config: {safe_config}")
```

### Performance

**DON'T fetch more data than needed**
```python
# ❌ BAD - Fetches all MRs then filters
all_mrs = await client.list_merge_requests(state="all", per_page=1000)
open_mrs = [mr for mr in all_mrs if mr['state'] == 'opened']

# ✅ GOOD - Filter server-side
open_mrs = await client.list_merge_requests(state="opened", per_page=20)
```

**DON'T make redundant API calls**
```python
# ❌ BAD - Fetches project info multiple times
project = await client.get_project()
# ... later ...
project = await client.get_project()  # Redundant!

# ✅ GOOD - Cache and reuse
project = await client.get_project()
self._cached_project = project
# ... later ...
project = self._cached_project
```

## Advanced Patterns

### Progressive Enhancement
Start simple, add features incrementally:
```
v1.0: Read-only tools (get, list)
v1.1: Basic write operations (create, update)
v2.0: Advanced search (grep, find)
v2.1: Automated workflows (review, deploy)
v3.0: Agent orchestration (parallel reviews)
v3.1: Interactive actions (approve, merge)
```

### Conditional Tool Execution
Make intelligent decisions based on data:
```python
# Get MR info
mr = await gitlab_get_merge_request(mr_id)

# Conditionally check pipelines
if mr.get('head_pipeline'):
    pipeline = await gitlab_get_pipeline(mr['head_pipeline']['id'])
    if pipeline['status'] == 'failed':
        # Fetch failing job logs
        jobs = await gitlab_list_jobs(pipeline['id'], scope=['failed'])
        for job in jobs:
            logs = await gitlab_get_job_log(job['id'])
            analyze_failure(logs)
```

### Multi-Service Orchestration
Coordinate tools from multiple MCP servers:
```python
# GitLab: Get MR details
mr = await gitlab_get_merge_request(123)

# Jira: Check if mentioned tickets exist
tickets = extract_ticket_ids(mr['description'])
for ticket_id in tickets:
    ticket = await jira_get_issue(ticket_id)
    validate_ticket_status(ticket)

# Slack: Notify reviewers
reviewers = mr['reviewers']
for reviewer in reviewers:
    await slack_send_message(reviewer['slack_id'], f"Please review MR !{mr['iid']}")
```

## Summary Checklist

**MCP Server Development:**
- [ ] Single-responsibility tools with clear names
- [ ] Comprehensive JSON schemas with descriptions
- [ ] Retry logic with exponential backoff
- [ ] Appropriate timeouts (10s connect, 20-30s max)
- [ ] Meaningful error messages with troubleshooting steps
- [ ] Secure credential management (600 permissions, .gitignore)
- [ ] Caching for expensive queries
- [ ] Pagination for list operations
- [ ] Test scripts covering all tools
- [ ] Clear README with setup instructions

**Workflow Design:**
- [ ] Multi-stage architecture with checkpoints
- [ ] TODO list tracking throughout workflow
- [ ] Parallel agent execution for independent tasks
- [ ] Focused agent responsibilities
- [ ] Unified result synthesis
- [ ] Clear progress indicators
- [ ] Interactive action options

**Slash Commands:**
- [ ] Clear argument hints
- [ ] Intelligent defaults
- [ ] Usage examples
- [ ] Error handling with helpful messages

**Configuration:**
- [ ] Project-specific with global fallback
- [ ] Validation on first use
- [ ] Never committed to version control
- [ ] Restrictive permissions (600)

By following these best practices, you'll create robust, secure, and user-friendly MCP integrations that significantly enhance Claude Code's capabilities.

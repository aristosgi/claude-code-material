# GitLab MCP Setup Workflow - Complete Walkthrough

This example demonstrates the complete process of setting up GitLab MCP integration from scratch, using the custom `gitlab_mcp_server` and `/gitlab-setup` command.

## Prerequisites

- Python 3.8+ installed
- Git repository connected to a GitLab instance
- GitLab personal access token with appropriate permissions

## Step 1: Install GitLab MCP Server Dependencies

```bash
# Navigate to the MCP server directory
cd gitlab_mcp_server/

# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python -c "import mcp; print('MCP SDK installed successfully')"
```

**What gets installed:**
- `mcp` - Model Context Protocol SDK for Python
- `asyncio` - Async I/O support (included in Python 3.7+)
- Standard library modules (json, subprocess, logging, etc.)

## Step 2: Create GitLab Personal Access Token

1. Log into your GitLab instance
2. Navigate to: **Settings → Access Tokens** (or **Preferences → Access Tokens**)
3. Create a new token with these scopes:
   - ✅ `api` - Full API access
   - ✅ `read_repository` - Read repository data
   - ✅ `write_repository` - Write repository data (for approve/merge actions)
4. Copy the generated token (you won't be able to see it again!)

**Token example:** `your-gitlab-token-here`

**Security Note:** Never commit this token to version control!

## Step 3: Configure Claude Code to Use the MCP Server

**Location of Claude Code Config:**
- **Windows**: `%APPDATA%\Roaming\Claude\config.json`
- **Linux**: `~/.config/claude/config.json`
- **Mac**: `~/Library/Application Support/Claude/config.json`

**Add the GitLab MCP server configuration:**

```json
{
  "mcpServers": {
    "gitlab": {
      "command": "python",
      "args": [
        "C:/absolute/path/to/claude-code-material-1/gitlab_mcp_server/server.py"
      ],
      "cwd": "C:/absolute/path/to/claude-code-material-1/gitlab_mcp_server"
    }
  }
}
```

**Important:**
- Use absolute paths (not relative paths)
- On Windows, use forward slashes (`/`) or escaped backslashes (`\\`)
- The `cwd` (current working directory) must point to the server directory

**Alternative configuration using uvx (recommended for production):**

```json
{
  "mcpServers": {
    "gitlab": {
      "command": "uvx",
      "args": ["--from", "C:/path/to/gitlab_mcp_server", "gitlab-mcp"],
      "env": {
        "GITLAB_TOKEN": "your_token_here",
        "GITLAB_URL": "https://your.gitlab.instance"
      }
    }
  }
}
```

## Step 4: Restart Claude Code

After modifying `config.json`, restart Claude Code to load the new MCP server configuration.

**Verify MCP server loaded:**
1. Open Claude Code
2. Type a message and look for available tools
3. You should see tools prefixed with `mcp__gitlab__*`

**Example tools:**
- `mcp__gitlab__gitlab_get_project`
- `mcp__gitlab__gitlab_list_merge_requests`
- `mcp__gitlab__gitlab_get_merge_request`

## Step 5: Run the `/gitlab-setup` Command

Now that the MCP server is configured, use the `/gitlab-setup` slash command to configure your project.

```bash
# Navigate to your project directory in Claude Code
cd /path/to/your/project

# Run the setup command with your token
/gitlab-setup --token your-gitlab-token-here
```

**What happens during `/gitlab-setup`:**

### Phase 1: Argument Parsing
```
Parsing arguments...
  Token: am18***6FxR (masked)
  URL: Not specified, will auto-detect
```

### Phase 2: Auto-Detection from Git Remote
```bash
Detecting GitLab URL from git remote...

$ git remote get-url origin
https://gitlab.company.com/team/my-project.git

✅ Detected URL: https://gitlab.company.com
✅ Detected path: team/my-project
✅ Detected name: my-project
```

### Phase 3: API Connectivity Test
```
Testing API connectivity...
Attempt 1/3...
  → curl -k -s --connect-timeout 10 --max-time 20 \
     -H "Authorization: Bearer $TOKEN" \
     https://gitlab.company.com/api/v4/version

Response: {"version": "15.8.2", "revision": "abc123"}
✅ Connected to GitLab 15.8.2
```

### Phase 4: Project ID Detection (Critical!)
```
Detecting Project ID...

Method 1: Direct access using URL-encoded path
  → curl -k -s -H "Authorization: Bearer $TOKEN" \
     https://gitlab.company.com/api/v4/projects/team%2Fmy-project

Response: {"id": 12345, "name": "my-project", "path_with_namespace": "team/my-project"}
✅ Project ID: 12345

(If Method 1 fails, falls back to search with exact path matching)
```

**Why exact path matching matters:**
- Project name search can return wrong project
- Example: Searching "my-project" might return:
  - `team/my-project` (correct)
  - `other-team/my-project-fork` (wrong!)
  - `legacy/my-project-old` (wrong!)
- Exact path `team/my-project` ensures correct project

### Phase 5: Project Access Validation
```
Validating project access...
  → curl -k -s -H "Authorization: Bearer $TOKEN" \
     https://gitlab.company.com/api/v4/projects/12345

Response: {"id": 12345, "name": "my-project", ...}
✅ Project access confirmed
```

### Phase 6: Configuration File Generation
```
Generating configuration file...

Creating .claude/.gitlab-config:
───────────────────────────────────────────────
# GitLab API Configuration for my-project
# Auto-generated by /gitlab-setup command
GITLAB_TOKEN=your-gitlab-token-here
GITLAB_URL=https://gitlab.company.com
PROJECT_ID=12345
PROJECT_NAME=my-project
PROJECT_PATH=team/my-project
# Created: 2025-01-15 10:30:00
───────────────────────────────────────────────
✅ Configuration file created
```

### Phase 7: Git Remote Configuration
```
Configuring Git remote with token authentication...
  → git remote set-url origin \
     https://oauth2:$TOKEN@gitlab.company.com/team/my-project.git

✅ Git remote configured (token-based auth)
```

**Why configure git remote:**
- Allows Claude Code to perform git operations (push, pull) without password prompts
- Uses OAuth2 token authentication
- Secure: Token is stored in git config, not committed to repo

### Phase 8: Security Hardening
```
Setting secure permissions...
  → chmod 600 .claude/.gitlab-config

Permissions set to: -rw------- (owner read/write only)
✅ Config file secured

Adding to .gitignore...
  → echo ".claude/.gitlab-config" >> .gitignore

✅ Config added to .gitignore (prevents accidental commits)
```

### Setup Complete!
```
✅ GitLab setup complete!

Configuration Summary:
  Project: my-project (ID: 12345)
  Path: team/my-project
  URL: https://gitlab.company.com
  Config file: .claude/.gitlab-config (permissions: 600)
  Status: ✅ Added to .gitignore

Next steps:
  1. Test configuration: /gitlab-setup --test
  2. Review merge requests: /mr-review_gitlab [mr-id]
  3. List MRs: Ask me "List open merge requests"
```

## Step 6: Test the Configuration

```bash
# Verify everything works
/gitlab-setup --test
```

**Test output:**
```
Testing GitLab configuration...

[1/4] Checking config file...
  ✅ Config file exists: .claude/.gitlab-config
  ✅ Permissions correct: 600

[2/4] Testing API connectivity...
  ✅ API reachable: https://gitlab.company.com/api/v4/version
  ✅ GitLab version: 15.8.2

[3/4] Testing authentication...
  ✅ Token valid
  ✅ User: john.doe

[4/4] Testing project access...
  ✅ Project accessible: my-project (ID: 12345)
  ✅ Access level: Maintainer (40)

🎉 All tests passed! GitLab MCP is ready to use.

Available MCP Tools:
  - gitlab_get_project
  - gitlab_list_merge_requests
  - gitlab_get_merge_request
  - gitlab_get_merge_request_changes
  - gitlab_get_file
  - gitlab_approve_merge_request
  - gitlab_merge_merge_request
  - gitlab_add_merge_request_note
  ... (17 tools total)
```

## Step 7: Use GitLab MCP Tools

Now that setup is complete, you can use GitLab MCP tools in Claude Code:

**Example 1: List open merge requests**
```
User: "List all open merge requests"

Claude Code uses: mcp__gitlab__gitlab_list_merge_requests(state="opened")

Output:
📋 Open Merge Requests (3)

!123 - Add authentication feature
  Author: john.doe | feature/auth → main | 5 files changed

!124 - Fix login bug
  Author: jane.smith | bugfix/login → main | 2 files changed

!125 - Update dependencies
  Author: bob.jones | chore/deps → main | 1 file changed
```

**Example 2: Get details of specific MR**
```
User: "Show me details of MR !123"

Claude Code uses: mcp__gitlab__gitlab_get_merge_request(mr_iid=123)

Output:
📋 MR !123: Add authentication feature
🔀 feature/auth → main
👤 Author: john.doe
📅 Created: 2025-01-14 14:30
📊 Status: opened
✅ Approvals: 0/2 required
🔄 Pipeline: passed

Description:
Implements JWT-based authentication with refresh tokens.

Changed Files (5):
  - auth/login.py (+120, -5)
  - auth/tokens.py (+80, -0) [new file]
  - tests/test_auth.py (+200, -10)
  - requirements.txt (+2, -0)
  - README.md (+15, -2)
```

**Example 3: Review a merge request**
```
User: "/mr-review_gitlab 123"

Claude Code orchestrates:
  1. mcp__gitlab__gitlab_get_merge_request(123)
  2. mcp__gitlab__gitlab_get_merge_request_changes(123)
  3. mcp__gitlab__gitlab_get_file(...) for each changed file
  4. Launches 3 specialized review agents in parallel
  5. Synthesizes results into comprehensive report

[Detailed review output - see mr-review-workflow.md example]
```

## Common Setup Issues and Solutions

### Issue 1: MCP Server Not Detected

**Symptoms:**
```
User: "List merge requests"
Claude Code: "I don't have access to GitLab tools"
```

**Solutions:**
1. **Check config.json syntax** - Must be valid JSON
   ```bash
   # Validate JSON
   python -c "import json; json.load(open('path/to/config.json'))"
   ```

2. **Verify absolute paths** in config.json
   ```json
   ❌ "args": ["./server.py"]  // Relative path
   ✅ "args": ["C:/full/path/to/server.py"]  // Absolute path
   ```

3. **Restart Claude Code** after config changes

4. **Test server manually**
   ```bash
   cd gitlab_mcp_server
   python server.py
   # Should wait for input (not exit immediately)
   # Press Ctrl+C to exit
   ```

### Issue 2: Project ID Detection Fails

**Symptoms:**
```
❌ Could not find project: team/my-project
   Please check:
   - Git remote URL
   - GitLab access token permissions
   - Project visibility settings
```

**Solutions:**
1. **Verify git remote**
   ```bash
   git remote get-url origin
   # Should output: https://gitlab.company.com/team/my-project.git
   ```

2. **Check token permissions**
   - Token must have `api` and `read_repository` scopes
   - Check token expiration date in GitLab

3. **Verify project access**
   ```bash
   curl -k -H "Authorization: Bearer $TOKEN" \
     https://gitlab.company.com/api/v4/projects/team%2Fmy-project
   ```

4. **Manually specify project ID**
   ```bash
   # Find project ID in GitLab UI (Settings → General)
   # Then add to config:
   echo "PROJECT_ID=12345" >> .claude/.gitlab-config
   ```

### Issue 3: Network Connectivity Problems

**Symptoms:**
```
⚠️ Attempt 1/3 failed: HTTP 000 (connection failed)
⚠️ Attempt 2/3 failed: HTTP 000 (connection failed)
❌ API connectivity failed after 3 attempts
```

**Solutions:**
1. **Check corporate proxy settings**
   ```bash
   # Set proxy environment variables
   export HTTP_PROXY=http://proxy.company.com:8080
   export HTTPS_PROXY=http://proxy.company.com:8080
   ```

2. **Verify SSL bypass** - The `-k` flag bypasses SSL verification
   ```bash
   curl -k https://gitlab.company.com/api/v4/version
   ```

3. **Increase timeout values** in `gitlab_api.py`:
   ```python
   # Change from:
   --max-time 20

   # To:
   --max-time 30
   ```

4. **Test basic connectivity**
   ```bash
   ping gitlab.company.com
   curl https://gitlab.company.com
   ```

### Issue 4: Token Authentication Fails

**Symptoms:**
```
❌ 401 Unauthorized
   Token invalid or expired
```

**Solutions:**
1. **Regenerate token** in GitLab with correct scopes:
   - `api` ✅
   - `read_repository` ✅
   - `write_repository` ✅ (for approve/merge)

2. **Check token format** - Should be 20 characters, alphanumeric
   ```
   ✅ your-gitlab-token-here
   ❌ Bearer am18LHwBCEso9bGVQYa6  // Don't include "Bearer"
   ```

3. **Test token directly**
   ```bash
   curl -k -H "Authorization: Bearer $TOKEN" \
     https://gitlab.company.com/api/v4/user
   # Should return your user info
   ```

## Global vs Project-Specific Configuration

### Project-Specific Setup (Recommended)
```bash
# Run in project directory
cd /path/to/project
/gitlab-setup --token TOKEN --project

# Creates: /path/to/project/.claude/.gitlab-config
```

**When to use:**
- Different tokens for different projects
- Different GitLab instances per project
- Project-specific permissions

### Global Setup
```bash
/gitlab-setup --token TOKEN --global

# Creates: ~/.claude/gitlab-config
```

**When to use:**
- Same GitLab instance for all projects
- Same token works for all projects
- Simpler configuration

### Configuration Priority
1. **Project-specific** (`.claude/.gitlab-config`) - Highest priority
2. **Global** (`~/.claude/gitlab-config`)
3. **Environment** (`$GITLAB_TOKEN`, `$GITLAB_URL`) - Lowest priority

## Next Steps

Once setup is complete, explore these workflows:

1. **MR Review Workflow** - See `mr-review-workflow.md`
2. **Custom MCP Server** - See `custom-mcp-server.md`
3. **Parallel Agents** - See `parallel-agent-execution.md`

## Summary

You've successfully:
- ✅ Installed GitLab MCP server dependencies
- ✅ Created GitLab personal access token
- ✅ Configured Claude Code MCP settings
- ✅ Ran `/gitlab-setup` for project configuration
- ✅ Validated setup with `/gitlab-setup --test`
- ✅ Learned to use GitLab MCP tools

Your Claude Code instance can now:
- Access GitLab API via 17+ MCP tools
- Review merge requests automatically
- Approve and merge MRs
- Read files from repository
- Monitor pipelines and jobs
- Search codebase
- And much more!

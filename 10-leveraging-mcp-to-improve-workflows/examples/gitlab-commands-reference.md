# GitLab MCP Slash Commands - Complete Reference

This document provides the complete implementation of the GitLab MCP slash commands with detailed explanations.

## Overview

The GitLab MCP integration includes two main slash commands:
1. **`/gitlab-setup`** - Configure GitLab API integration
2. **`/mr-review_gitlab`** - Review merge requests with specialized agents

Both commands are located in `.claude/commands/` and demonstrate best practices for MCP-powered workflows.

---

## Command 1: `/gitlab-setup`

**File:** `.claude/commands/gitlab-setup.md`

### Complete Implementation

```markdown
---
allowed-tools: mcp__gitlab__*, Bash, Read, Write
argument-hint: [--token <token>] [--url <gitlab-url>] [--global] [--project] [--test]
description: Configure GitLab API integration for any project with automatic detection
---

Configure GitLab API integration for any project with automatic detection.

## Usage
```bash
/gitlab-setup [options]
```

## Arguments
- `--token <token>` - Optional: GitLab API token (will prompt if not provided)
- `--url <gitlab-url>` - Optional: GitLab instance URL (auto-detected from git remote)
- `--global` - Flag: Save to global config (~/.claude/gitlab-config)
- `--project` - Flag: Save to project config (.claude/.gitlab-config)
- `--test` - Flag: Test the configuration after setup

## Examples
```bash
# Auto-setup using git remote detection
/gitlab-setup --token your-gitlab-token-here

# Setup with custom GitLab URL
/gitlab-setup --token <token> --url https://gitlab.company.com

# Save globally for all projects
/gitlab-setup --token <token> --global

# Test existing configuration
/gitlab-setup --test
```

## Implementation Steps

1. **Parse arguments** - Extract token, flags from command line
2. **Auto-detect GitLab URL** from `git remote get-url origin`
3. **Test API connectivity** with provided token (with retry logic)
4. **CRITICAL: Auto-detect Project ID using EXACT PATH MATCH** (not just project name)
5. **Validate project ID** by making test API call
6. **Generate .gitlab-config** with all detected settings
7. **Secure permissions** - Set 600 on config file
8. **Add to .gitignore** - Ensure config never gets committed

## ⚠️ Critical Issues to Avoid

### Project ID Detection Problems
**Issue:** Using project name search can return wrong project (e.g., "cosmote-testing-lovable-ui" vs "cosmote-testing")

**Solution:** Use exact path matching instead of name search:
```bash
# ❌ WRONG - searches by name only
PROJECT_ID=$(curl ... "$URL/api/v4/projects?search=$PROJECT_NAME")

# ✅ CORRECT - searches by exact path
PROJECT_PATH=$(echo "$REMOTE_URL" | sed 's|\.git$||' | sed 's|.*/\([^/]*/[^/]*\)$|\1|')
PROJECT_ID=$(curl ... "$URL/api/v4/projects?search=$PROJECT_PATH" | \
    grep -B2 -A2 "\"path_with_namespace\":\"$PROJECT_PATH\"" | \
    grep '"id":' | head -1 | grep -o '[0-9]*')
```

### Network Connectivity Issues
**Issue:** Corporate networks may cause intermittent API failures (HTTP 000 responses)

**Solution:** Add retry logic and better error handling:
```bash
# Test connectivity with retries
test_api_connectivity() {
    for i in {1..3}; do
        RESPONSE=$(curl -k -s --connect-timeout 10 --max-time 20 \
            -H "Authorization: Bearer $TOKEN" \
            "$URL/api/v4/version" 2>&1)

        if echo "$RESPONSE" | grep -q '"version"'; then
            echo "✅ API connectivity confirmed"
            return 0
        else
            echo "⚠️ Attempt $i failed: $RESPONSE"
            sleep 2
        fi
    done
    echo "❌ API connectivity failed after 3 attempts"
    return 1
}
```

## Actual Implementation

```bash
# Parse arguments
TOKEN=${args[--token]}
URL=${args[--url]}
TEST_ONLY=${args[--test]}

# Auto-detect from git remote
if [ -z "$URL" ]; then
    REMOTE_URL=$(git remote get-url origin 2>/dev/null)
    URL=$(echo "$REMOTE_URL" | sed 's|^\(https\?://[^/]*\).*|\1|')
    PROJECT_PATH=$(echo "$REMOTE_URL" | sed 's|\.git$||' | sed 's|.*/\([^/]*/[^/]*\)$|\1|')
    PROJECT_NAME=$(echo "$PROJECT_PATH" | sed 's|.*/||')
fi

# Test API and get project ID using exact path
# First try direct access using URL-encoded path
PROJECT_ID=$(curl -k -s -H "Authorization: Bearer $TOKEN" \
    "$URL/api/v4/projects/$(echo "$PROJECT_PATH" | sed 's|/|%2F|g')" | \
    grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)

# If direct access fails, fall back to search with exact path matching
if [ -z "$PROJECT_ID" ]; then
    PROJECT_ID=$(curl -k -s -H "Authorization: Bearer $TOKEN" \
        "$URL/api/v4/projects?search=$PROJECT_PATH" | \
        grep -B2 -A2 "\"path_with_namespace\":\"$PROJECT_PATH\"" | \
        grep '"id":' | head -1 | grep -o '[0-9]*')
fi

# Validate project ID was found
if [ -z "$PROJECT_ID" ]; then
    echo "❌ Could not find project: $PROJECT_PATH"
    echo "   Please check:"
    echo "   - Git remote URL: $REMOTE_URL"
    echo "   - GitLab access token permissions"
    echo "   - Project visibility settings"
    exit 1
fi

# Validate project access
echo "Validating project access..."
PROJECT_VALIDATION=$(curl -k -s -H "Authorization: Bearer $TOKEN" \
    "$URL/api/v4/projects/$PROJECT_ID" | grep '"name"')
if [ -z "$PROJECT_VALIDATION" ]; then
    echo "❌ Cannot access project ID $PROJECT_ID"
    exit 1
fi

# Generate config file
cat > .claude/.gitlab-config << EOF
# GitLab API Configuration for $PROJECT_NAME
# Auto-generated by /gitlab-setup command
GITLAB_TOKEN=$TOKEN
GITLAB_URL=$URL
PROJECT_ID=$PROJECT_ID
PROJECT_NAME=$PROJECT_NAME
PROJECT_PATH=$PROJECT_PATH
# Created: $(date)
EOF

# Configure Git remote with token for authentication
echo "Configuring Git remote with token authentication..."
git remote set-url origin "https://oauth2:$TOKEN@$(echo "$URL" | sed 's|https://||')/$PROJECT_PATH.git"
echo "✅ Git remote configured with token authentication"

# Secure permissions and gitignore
chmod 600 .claude/.gitlab-config
echo ".claude/.gitlab-config" >> .gitignore

echo "✅ GitLab setup complete!"
echo ""
echo "Configuration:"
echo "  Project: $PROJECT_NAME (ID: $PROJECT_ID)"
echo "  Path: $PROJECT_PATH"
echo "  URL: $URL"
echo ""
echo "Config file: .claude/.gitlab-config (permissions: 600)"
echo "Added to .gitignore to prevent accidental commits"
```

## Configuration Priority
1. Project-specific: `.claude/.gitlab-config`
2. Global: `~/.claude/gitlab-config`
3. Environment: `$GITLAB_TOKEN`, `$GITLAB_URL`

## Config File Structure
```bash
# GitLab API Configuration
GITLAB_TOKEN=<token>
GITLAB_URL=<url>
PROJECT_ID=<id>
PROJECT_NAME=<name>
```

## Integration with /mr-review
Once configured, `/mr-review` automatically gains API capabilities:
- `--approve` - Approve the merge request
- `--comment` - Post review results as MR comment
- `--merge` - Merge the MR after successful review
```

### Key Features Explained

#### 1. Frontmatter Metadata
```yaml
---
allowed-tools: mcp__gitlab__*, Bash, Read, Write
argument-hint: [--token <token>] [--url <gitlab-url>] [--global] [--project] [--test]
description: Configure GitLab API integration for any project with automatic detection
---
```

- **`allowed-tools`**: Restricts which Claude Code tools this command can use (security)
- **`argument-hint`**: Shows users the expected command syntax
- **`description`**: Brief description shown in command list

#### 2. Auto-Detection Logic

**Extracts GitLab URL from git remote:**
```bash
REMOTE_URL=$(git remote get-url origin)
# Example: https://gitlab.company.com/team/project.git

URL=$(echo "$REMOTE_URL" | sed 's|^\(https\?://[^/]*\).*|\1|')
# Result: https://gitlab.company.com
```

**Extracts project path:**
```bash
PROJECT_PATH=$(echo "$REMOTE_URL" | sed 's|\.git$||' | sed 's|.*/\([^/]*/[^/]*\)$|\1|')
# Result: team/project
```

#### 3. Exact Path Matching (Critical!)

**Why it matters:**
- Project name "my-project" could match multiple projects:
  - `team-a/my-project` (correct)
  - `team-b/my-project-old` (wrong!)
  - `archive/my-project-backup` (wrong!)

**Solution:**
```bash
# URL-encode the full path: team/project → team%2Fproject
PROJECT_ID=$(curl "$URL/api/v4/projects/team%2Fproject")

# Or search with exact path validation
PROJECT_ID=$(curl "$URL/api/v4/projects?search=team/project" | \
    grep "\"path_with_namespace\":\"team/project\"")
```

#### 4. Security Hardening

**Restrictive permissions:**
```bash
chmod 600 .claude/.gitlab-config
# Result: -rw------- (owner read/write only)
```

**Automatic .gitignore:**
```bash
echo ".claude/.gitlab-config" >> .gitignore
# Prevents accidental token commits
```

---

## Command 2: `/mr-review_gitlab`

**File:** `.claude/commands/mr-review_gitlab.md`

### Complete Implementation

```markdown
---
allowed-tools: mcp__gitlab__*, Read, Bash(git *), Grep, TodoWrite, Task
argument-hint: [mr-id|HEAD] [--source branch] [--target branch] [--config config-file] [--comment] [--approve] [--merge] [--verbose] [--files-only]
description: Review a GitLab merge request against team requirements using GitLab MCP
---

# MR Review Command (GitLab MCP Version)

You are tasked with reviewing GitLab merge request $1 against the team's requirements using GitLab MCP tools instead of manual curl commands.

## Your Task:
Review the specified merge request thoroughly and provide actionable feedback based on the team's coding standards and requirements.

## Step-by-Step Process:

### 1. Parse Arguments and Setup
First, understand the arguments provided:
- **MR ID**: $1 (if it's a number like 123, !456, etc.)
- **Arguments**: $ARGUMENTS (parse for flags like --verbose, --approve, etc.)

Create a todo list to track your progress through the review process.

### 2. Get MR Information Using MCP Tools
Use the GitLab MCP tools to gather information:
- Use `mcp__gitlab__gitlab_get_merge_request` with the MR IID to get basic details
- Use `mcp__gitlab__gitlab_get_merge_request_changes` to get the file changes and diffs
- Extract the source and target branches from the MR details

Display a summary like:
```
📋 MR !123: Add new authentication feature
🔀 feature/auth-improvements → main
👤 Author: Developer Name
📊 Status: opened
```

### 3. Analyze Changed Files
For each changed file from the MR changes:
- Use `mcp__gitlab__gitlab_get_file` to get the current file content from the source branch
- If needed, also get the file content from the target branch for comparison
- Focus your analysis only on the files that actually changed

### 4. Load and Apply Requirements
Read the requirements file (default: `.claude/.mr-requirements.md` or use --config flag):
- Use the `Read` tool to load the requirements
- Apply each requirement category to the changed files only

### 5. Launch Specialized Review Agents in Parallel
After gathering MR information and changed files, launch three specialized review agents simultaneously using the Task tool:

**Agent 1: Code Quality Review**
```
Use Task tool with subagent_type: "code-quality-reviewer"
Prompt: "Review the code quality for MR !{mr_id}. Analyze these changed files: {list_of_changed_files}. Focus on coding standards, print statements, TODO comments, code structure, and production code issues."
```

**Agent 2: Documentation Review**
```
Use Task tool with subagent_type: "documentation-reviewer"
Prompt: "Review the documentation for MR !{mr_id}. Check function/class docstrings in these changed files: {list_of_changed_files}. Ensure all public methods have proper documentation."
```

**Agent 3: Project Documentation Review**
```
Use Task tool with subagent_type: "readme-reviewer"
Prompt: "Review if project documentation needs updates for MR !{mr_id}. Based on changes in files: {list_of_changed_files}, check if README, CHANGELOG, or other project docs need updates."
```

**Additional Manual Checks:**
- Review commit messages using `git log` commands for conventional format
- Check branch naming conventions
- Verify security issues (hardcoded secrets, SQL injection, unsafe operations)

### 6. Synthesize Results from All Agents
Wait for all three agents to complete, then:
1. Collect findings from code-quality-reviewer agent
2. Collect findings from documentation-reviewer agent
3. Collect findings from readme-reviewer agent
4. Combine results with manual checks (git standards, security)

### 7. Generate Unified Review Report
Provide a comprehensive structured report with:
- **Overall MR Status**: PASS/FAIL with overall score
- **Agent-Specific Findings**:
  - Code Quality Score and issues (from code-quality-reviewer)
  - Documentation Score and gaps (from documentation-reviewer)
  - Project Documentation Status (from readme-reviewer)
- **Manual Check Results**: Git standards, security, branch naming
- **Aggregated Issues**: All issues sorted by priority (CRITICAL/HIGH/MEDIUM/LOW)
- **Specific file:line references** for each issue
- **Actionable recommendations** with clear next steps
- **Priority matrix** showing which issues must be fixed vs. should be fixed

### 8. Interactive Actions
After completing the review, check what the user wants to do:
- If --approve flag was passed, they want to approve
- If --merge flag was passed, they want to merge
- If --comment flag was passed, they want to add a comment
- If no flags, ask them interactively

For interactive mode:
1. Get project details using `mcp__gitlab__gitlab_get_project` to understand user permissions
2. Offer appropriate actions based on their access level:
   - Developer level (30+): Can approve
   - Maintainer level (40+): Can approve and merge
3. If they choose to take action, provide the appropriate response format they can use

### 9. Use Available MCP Tools Only
**Available MCP tools:**
- `mcp__gitlab__gitlab_get_project` - Get project details
- `mcp__gitlab__gitlab_get_merge_request` - Get MR details
- `mcp__gitlab__gitlab_get_merge_request_changes` - Get MR file changes
- `mcp__gitlab__gitlab_get_file` - Get file content from repository

**For actions not yet in MCP:**
- Provide the user with clear instructions on how to approve/merge/comment using the GitLab UI
- Or provide them with the exact curl commands they could run if needed

## Important Guidelines:
- **Focus only on changed files** - don't analyze the entire codebase
- **Use specific file:line references** when reporting issues
- **Be actionable** - provide clear steps to fix each issue
- **Be efficient** - batch similar checks together
- **Update your todo list** as you progress through each step
- **Handle errors gracefully** - if a file can't be read, note it and continue

## Example Workflow:
1. "Reviewing MR !456: Refactor user authentication module"
2. Get MR details and changes via MCP
3. Found 3 changed files: `auth/login.py`, `auth/utils.py`, `tests/test_auth.py`
4. Analyze each file content for quality, security, documentation
5. Generate report with specific findings
6. Ask user what action they want to take

Remember: You are providing instructions to Claude on how to conduct the review using the available MCP tools, not executing bash scripts or Python code directly.
```

### Key Features Explained

#### 1. Allowed Tools Specification
```yaml
allowed-tools: mcp__gitlab__*, Read, Bash(git *), Grep, TodoWrite, Task
```

- **`mcp__gitlab__*`**: All GitLab MCP tools (17+ tools)
- **`Read`**: Read local files (requirements, config)
- **`Bash(git *)`**: Only git commands (not full bash access)
- **`Grep`**: Search files for patterns
- **`TodoWrite`**: Track workflow progress
- **`Task`**: Launch specialized subagents

#### 2. Multi-Stage Workflow

**Stage 1-4: Data Gathering**
- Parse arguments
- Fetch MR details via MCP tools
- Get file changes and content
- Load review requirements

**Stage 5: Parallel Agent Execution**
```
Agent 1 (code-quality-reviewer)    ┐
                                    ├─ Run in parallel
Agent 2 (documentation-reviewer)   │
                                    ├─ 3x faster than sequential
Agent 3 (readme-reviewer)          ┘
```

**Stage 6-7: Synthesis & Reporting**
- Collect all agent findings
- Combine with manual checks
- Generate unified report

**Stage 8: Interactive Actions**
- Present options to user
- Execute approved actions via MCP

#### 3. Agent Orchestration

**Launching agents in parallel:**
```markdown
Use Task tool with subagent_type: "code-quality-reviewer"
Prompt: "Review the code quality for MR !{mr_id}..."
```

**Why parallel execution:**
- **Speed**: 3 agents complete in ~30s vs. ~90s sequential
- **Specialization**: Each agent focuses on its domain
- **Scalability**: Easy to add more review dimensions

#### 4. MCP Tool Usage

**Get MR basic details:**
```
mcp__gitlab__gitlab_get_merge_request(mr_iid=123)
→ Returns: title, description, author, status, branches
```

**Get file changes:**
```
mcp__gitlab__gitlab_get_merge_request_changes(mr_iid=123)
→ Returns: array of changed files with diffs
```

**Get file content:**
```
mcp__gitlab__gitlab_get_file(file_path="auth/login.py", ref="feature/auth")
→ Returns: base64-decoded file content
```

---

## Command Usage Examples

### Example 1: Basic Setup
```bash
# Clone a GitLab project
git clone https://gitlab.company.com/team/project.git
cd project

# Setup GitLab MCP integration
/gitlab-setup --token your-gitlab-token-here

# Output:
# ✅ GitLab setup complete!
# Configuration:
#   Project: project (ID: 12345)
#   Path: team/project
#   URL: https://gitlab.company.com
```

### Example 2: Basic MR Review
```bash
# Review merge request !123
/mr-review_gitlab 123

# Claude Code will:
# 1. Fetch MR details
# 2. Get changed files
# 3. Launch 3 review agents in parallel
# 4. Generate comprehensive report
# 5. Ask for next action
```

### Example 3: Review and Approve
```bash
# Review and immediately approve if passing
/mr-review_gitlab 123 --approve

# If review passes:
#   ✅ MR !123 approved
# If review fails:
#   ⚠️ Cannot approve - 3 critical issues found
#   Please address issues first
```

### Example 4: Review, Approve, and Merge
```bash
# Full workflow: review → approve → merge
/mr-review_gitlab 123 --approve --merge

# Output:
# ✅ Review complete (Score: 95/100)
# ✅ MR !123 approved
# ✅ MR !123 merged into main
# ✅ Source branch deleted
```

### Example 5: Post Review as Comment
```bash
# Add review results as MR comment
/mr-review_gitlab 123 --comment

# Creates a detailed comment on the MR with:
# - Overall status and score
# - All findings by category
# - Specific file:line references
# - Actionable recommendations
```

---

## Next Steps

See related examples:
- `gitlab-agents-reference.md` - Complete agent implementations
- `parallel-agent-execution.md` - Agent orchestration patterns
- `mr-review-workflow.md` - End-to-end review walkthrough
- `gitlab-mcp-setup-workflow.md` - Setup process details

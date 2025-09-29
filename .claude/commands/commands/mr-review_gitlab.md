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
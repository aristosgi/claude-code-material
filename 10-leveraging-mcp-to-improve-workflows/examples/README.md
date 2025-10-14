# GitLab MCP Examples - Complete Reference

This directory contains complete, production-ready implementations of GitLab MCP integration for Claude Code, including commands, agents, and the MCP server itself.

## Directory Structure

```
examples/
├── README.md                              # This file - index of all examples
│
├── commands/                              # Slash command implementations
│   ├── gitlab-setup.md                   # Configure GitLab API integration
│   └── mr-review_gitlab.md               # Review merge requests with agents
│
├── agents/                                # Specialized review agent implementations
│   ├── code-quality-reviewer.md          # Code quality and standards analysis
│   ├── documentation-reviewer.md         # Docstring completeness review
│   └── readme-reviewer.md                # README update requirement checker
│
├── gitlab-mcp-setup-workflow.md          # Complete setup walkthrough
├── mr-review-workflow.md                 # End-to-end review example
├── gitlab-mcp-server-implementation.md   # MCP server architecture guide
├── gitlab-commands-reference.md          # Command usage reference
├── gitlab-agents-reference.md            # Agent behavior reference
└── parallel-agent-execution.md           # Agent orchestration patterns
```

---

## Quick Start Guide

### 1. Setup GitLab MCP Integration

**Prerequisites:**
- Python 3.8+ installed
- GitLab personal access token
- Git repository connected to GitLab

**Steps:**
1. Install MCP server dependencies (see `gitlab-mcp-setup-workflow.md`)
2. Configure Claude Code to use MCP server
3. Run `/gitlab-setup --token YOUR_TOKEN` command
4. Test with `/gitlab-setup --test`

**See:** `gitlab-mcp-setup-workflow.md` for detailed walkthrough

### 2. Review a Merge Request

**Command:**
```bash
/mr-review_gitlab 123
```

**What happens:**
1. Fetches MR details via MCP tools
2. Launches 3 specialized agents in parallel
3. Generates comprehensive review report
4. Offers interactive actions (approve/merge/comment)

**See:** `mr-review-workflow.md` for complete example

---

## Component Reference

### Commands (Slash Commands)

#### `/gitlab-setup`
**File:** `commands/gitlab-setup.md`

**Purpose:** Configure GitLab API integration with automatic project detection

**Usage:**
```bash
# Auto-detect from git remote
/gitlab-setup --token your-gitlab-token-here

# Custom GitLab URL
/gitlab-setup --token TOKEN --url https://gitlab.company.com

# Global configuration
/gitlab-setup --token TOKEN --global

# Test configuration
/gitlab-setup --test
```

**Key Features:**
- Auto-detects GitLab URL from git remote
- Exact path matching for project ID (prevents wrong project selection)
- Retry logic for network reliability
- Secure config file generation (600 permissions)
- Automatic .gitignore integration

**Critical Implementation:**
- Uses exact path matching instead of name search
- Handles corporate network issues (SSL bypass, retry logic)
- Validates project access before generating config

---

#### `/mr-review_gitlab`
**File:** `commands/mr-review_gitlab.md`

**Purpose:** Review GitLab merge requests with specialized agents and MCP tools

**Usage:**
```bash
# Basic review
/mr-review_gitlab 123

# Review with specific branches
/mr-review_gitlab 123 --source feature/auth --target main

# Review and approve
/mr-review_gitlab 123 --approve

# Review, approve, and merge
/mr-review_gitlab 123 --approve --merge

# Post review as comment
/mr-review_gitlab 123 --comment

# Verbose output
/mr-review_gitlab 123 --verbose
```

**Key Features:**
- Multi-stage workflow (8 stages)
- Parallel agent execution (3 specialized agents)
- MCP tool integration (17+ GitLab tools)
- Unified report generation
- Interactive action options

**Workflow Stages:**
1. Parse arguments and setup
2. Get MR information via MCP
3. Analyze changed files
4. Load review requirements
5. Launch agents in parallel (code quality, docs, README)
6. Synthesize results
7. Generate unified report
8. Present interactive options

---

### Agents (Specialized Review Agents)

#### Code Quality Reviewer
**File:** `agents/code-quality-reviewer.md`

**Purpose:** Analyze code quality, standards, and production code issues

**Focus Areas:**
- Code structure and best practices
- Production code issues (print statements, TODOs, debug code)
- Coding standards (naming, formatting, complexity)
- Performance concerns

**Output:**
- Quality score (0-100)
- Issues by severity (CRITICAL/HIGH/MEDIUM/LOW)
- Specific file:line references
- Suggested fixes

**Example Finding:**
```
[MEDIUM] Debug print statement
  File: auth/login.py:127
  Issue: print(f"Token generated: {token}")
  Fix: Replace with logging: logger.debug(...)
  Category: Production Code Issue
```

---

#### Documentation Reviewer
**File:** `agents/documentation-reviewer.md`

**Purpose:** Ensure comprehensive function/class documentation

**Focus Areas:**
- Function docstrings (all public functions)
- Parameter and return value documentation
- Class-level docstrings
- Module documentation
- Documentation quality and consistency

**Output:**
- Documentation coverage percentage
- Quality rating (Excellent/Good/Needs Improvement/Poor)
- Missing docstrings (CRITICAL)
- Inadequate documentation (HIGH)

**Example Finding:**
```
Missing Documentation [CRITICAL]
  ❌ auth/tokens.py:generate_access_token (line 18)
  ❌ auth/tokens.py:generate_refresh_token (line 45)

Documentation Coverage: 68% (15/22 public functions)
Target: 100%
```

---

#### README Reviewer
**File:** `agents/readme-reviewer.md`

**Purpose:** Determine if README.md needs updates based on code changes

**Focus Areas:**
- New features requiring documentation
- Installation/setup changes (new dependencies)
- Configuration changes (environment variables)
- Breaking changes to public APIs
- Usage example updates

**Decision Criteria:**
- **YES**: New public APIs, dependencies, breaking changes, configuration
- **NO**: Internal refactoring, bug fixes, test changes

**Example Output:**
```
README Impact Assessment
  Change Type: Major Feature Refactor
  User Impact: HIGH
  README Update Needed: YES

Specific Sections to Update:
1. Authentication Section - JWT tokens (not sessions)
2. Configuration - JWT_SECRET_KEY required
3. Migration Guide - Session to JWT migration
```

---

## Detailed Guides

### Setup and Configuration

**`gitlab-mcp-setup-workflow.md`**
- Step-by-step setup from scratch
- Prerequisites and installation
- Configuration walkthrough
- Troubleshooting common issues
- Testing and validation

### Workflow Examples

**`mr-review-workflow.md`**
- End-to-end MR review scenario
- Real timing data (50 seconds total)
- Agent execution details
- Report generation
- Interactive action handling

### Architecture and Implementation

**`gitlab-mcp-server-implementation.md`**
- MCP server architecture (`gitlab_mcp_server/`)
- 17+ tool implementations
- API client design (curl-based approach)
- Key implementation decisions
- Corporate network compatibility

### Reference Documentation

**`gitlab-commands-reference.md`**
- Complete command implementations
- Usage examples
- Key features explained
- Integration patterns

**`gitlab-agents-reference.md`**
- Complete agent implementations
- Behavior and focus areas
- Output formats
- Creating custom agents

**`parallel-agent-execution.md`**
- Orchestration patterns
- Performance analysis (3x speedup)
- Agent independence
- Error handling
- Advanced patterns

---

## Usage Patterns

### Pattern 1: Setup Once, Use Everywhere

```bash
# One-time setup
/gitlab-setup --token YOUR_TOKEN

# Use in any project
cd project-a && /mr-review_gitlab 123
cd project-b && /mr-review_gitlab 456
```

### Pattern 2: Automated MR Review

```bash
# Review every MR before merging
/mr-review_gitlab 123

# If passes, approve and merge
/mr-review_gitlab 123 --approve --merge

# If needs work, post review as comment
/mr-review_gitlab 123 --comment
```

### Pattern 3: Custom Review Requirements

```bash
# Use custom requirements file
/mr-review_gitlab 123 --config .claude/team-standards.md

# Requirements file defines:
# - Code quality standards
# - Documentation requirements
# - Security checks
# - Testing standards
```

---

## File Locations in Project

### Production Files (Used by Claude Code)

```
.claude/
├── commands/
│   ├── gitlab-setup.md              # Active command
│   └── mr-review_gitlab.md          # Active command
└── agents/
    ├── code-quality-reviewer.md     # Active agent
    ├── documentation-reviewer.md    # Active agent
    └── readme-reviewer.md           # Active agent

gitlab_mcp_server/                   # Active MCP server
├── server.py
├── gitlab_api.py
├── requirements.txt
└── README.md
```

### Reference Files (Documentation)

```
10-leveraging-mcp-to-improve-workflows/
├── README.md                        # Main section documentation
├── DOS.md                           # Best practices
└── examples/                        # ← You are here
    ├── README.md                    # This file
    ├── commands/                    # Command copies for reference
    ├── agents/                      # Agent copies for reference
    └── *.md                         # Detailed guides
```

---

## Key Concepts

### MCP Tools

MCP tools are functions exposed by the MCP server that Claude Code can call:

```
mcp__gitlab__gitlab_get_merge_request(mr_iid=123)
→ Returns: MR details (title, author, branches, status, etc.)

mcp__gitlab__gitlab_get_merge_request_changes(mr_iid=123)
→ Returns: Changed files with diffs

mcp__gitlab__gitlab_get_file(file_path="auth/login.py", ref="feature/auth")
→ Returns: File content (base64-decoded)
```

### Slash Commands

Slash commands are custom workflows defined in `.claude/commands/*.md`:

- Start with `/` (e.g., `/gitlab-setup`, `/mr-review_gitlab`)
- Can use MCP tools, subagents, and other Claude Code tools
- Frontmatter defines allowed tools and arguments

### Subagents

Subagents are specialized Claude Code instances for focused tasks:

- Defined in `.claude/agents/*.md`
- Have specific tool access and responsibilities
- Run in isolated environments
- Can be launched in parallel

### Parallel Execution

Multiple agents run simultaneously for speed:

```
Sequential (90s):    Agent1 → Agent2 → Agent3
Parallel (30s):      Agent1 ┐
                     Agent2 ├─ All run at once
                     Agent3 ┘
```

**Requirement:** All `Task` calls must be in single message

---

## Advanced Topics

### Extending the MCP Server

Add new GitLab tools by:
1. Defining tool in `server.py` (`@app.list_tools()`)
2. Implementing handler in `gitlab_api.py`
3. Adding route in `server.py` (`@app.call_tool()`)

See `gitlab-mcp-server-implementation.md` for details.

### Creating Custom Agents

Template for new review agents:

```markdown
---
name: your-agent-name
description: MUST BE USED when [condition]
tools: Read, Grep, mcp__gitlab__*
---

You are a specialized [domain] reviewer.

## Your Focus Areas:
1. [Area 1]
2. [Area 2]

## Output Format:
[Structured output]

## What to IGNORE:
[What other agents handle]
```

See `gitlab-agents-reference.md` for examples.

### Workflow Orchestration Patterns

1. **Parallel Analysis**: Multiple independent analyses of same data
2. **Divide and Conquer**: Split large task across agents
3. **Multi-Stage Pipeline**: Sequential stages with parallel within
4. **Specialist + Generalist**: Focused agents + synthesis agent

See `parallel-agent-execution.md` for details.

---

## Troubleshooting

### MCP Server Not Detected

**Check:**
1. `config.json` syntax (valid JSON)
2. Absolute paths in configuration
3. Restart Claude Code after changes

**See:** `gitlab-mcp-setup-workflow.md` → "Troubleshooting"

### Project ID Detection Issues

**Problem:** Wrong project or "Project not found"

**Solution:** Uses exact path matching

**See:** `commands/gitlab-setup.md` → "Critical Issues to Avoid"

### Agent Not Running

**Check:**
1. Agent name matches file (e.g., `code-quality-reviewer`)
2. Agent frontmatter has correct `tools:` list
3. `Task` calls are in single message (for parallel)

**See:** `gitlab-agents-reference.md` → "Agent Behavior"

---

## Summary

This examples directory provides:

✅ **Complete implementations** - Production-ready commands and agents
✅ **Detailed walkthroughs** - Step-by-step guides
✅ **Reference documentation** - Command and agent references
✅ **Architecture guides** - MCP server implementation details
✅ **Best practices** - Learned from real-world usage

All files are ready to use or adapt for your own MCP integrations!

---

## Next Steps

1. **Setup**: Follow `gitlab-mcp-setup-workflow.md`
2. **Try it**: Run `/mr-review_gitlab` on a test MR
3. **Customize**: Adapt commands/agents for your needs
4. **Extend**: Add new tools to MCP server

For questions or issues, refer to the main section documentation in the parent directory's `README.md`.

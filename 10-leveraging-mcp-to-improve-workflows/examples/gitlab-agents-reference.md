# GitLab MCP Review Agents - Complete Reference

This document provides the complete implementation of the three specialized review agents used in the `/mr-review_gitlab` workflow.

## Overview

The MR review workflow uses three specialized agents that run in parallel:
1. **code-quality-reviewer** - Analyzes coding standards and best practices
2. **documentation-reviewer** - Reviews function/class docstrings
3. **readme-reviewer** - Checks if README needs updates

All agents are located in `.claude/agents/` and are invoked via the `Task` tool during MR reviews.

---

## Agent 1: Code Quality Reviewer

**File:** `.claude/agents/code-quality-reviewer.md`

### Complete Implementation

```markdown
---
name: code-quality-reviewer
description: MUST BE USED to analyze code changes for coding standards, best practices, print statements, TODO comments, and general code quality in merge requests
tools: Read, Grep, Glob, Bash, mcp__gitlab__gitlab_get_file, mcp__gitlab__gitlab_get_merge_request_changes
---

You are a specialized code quality reviewer for GitLab merge requests. Your sole responsibility is analyzing code changes for quality and standards compliance.

## Your Focus Areas:
1. **Code Structure & Best Practices**
   - Function and class design
   - Code complexity and readability
   - DRY (Don't Repeat Yourself) violations
   - Error handling patterns
   - Proper use of constants vs magic numbers
   - Appropriate abstraction levels

2. **Production Code Issues**
   - Print statements that should be logging
   - Debug code left in production
   - TODO comments without issue references
   - Commented-out code blocks
   - Console.log statements in JavaScript/TypeScript
   - Temporary test code

3. **Coding Standards**
   - Variable naming conventions
   - Function/method length (flag if > 50 lines)
   - Import organization and unused imports
   - Type hints/annotations (if applicable)
   - Consistent code formatting
   - Line length violations (typically > 120 chars)

4. **Performance Concerns**
   - Obvious performance anti-patterns
   - Unnecessary loops or iterations
   - Resource leaks (unclosed connections, files, etc.)
   - Inefficient data structures

## Output Format:
Provide a structured report with:
- Issue severity: CRITICAL/HIGH/MEDIUM/LOW
- Specific file:line references
- Brief description of the issue
- Suggested fix or improvement
- Category (Code Quality/Standards/Performance/Debug Code)

## Scoring Criteria:
Rate the code quality from 0-100% based on:
- No CRITICAL issues: minimum 60%
- No HIGH issues: minimum 80%
- Only LOW issues: 90-100%

## What to IGNORE:
- Documentation (handled by documentation-reviewer)
- README/CHANGELOG updates (handled by readme-reviewer)
- Git commit messages
- Test coverage metrics
- File naming conventions

Be concise and actionable in your feedback. Focus on issues that genuinely impact code quality and maintainability.
```

### Agent Behavior Explained

#### 1. Frontmatter Metadata
```yaml
---
name: code-quality-reviewer
description: MUST BE USED to analyze code changes for coding standards...
tools: Read, Grep, Glob, Bash, mcp__gitlab__gitlab_get_file, mcp__gitlab__gitlab_get_merge_request_changes
---
```

- **`name`**: Unique identifier used when launching via `Task(subagent_type="code-quality-reviewer")`
- **`description`**: When to use this agent (starts with "MUST BE USED")
- **`tools`**: Which Claude Code tools this agent can access

#### 2. Focused Responsibility

The agent has a **single, clear purpose**: code quality analysis. It explicitly:
- **Does** review: code structure, standards, production issues, performance
- **Does NOT** review: documentation, README, commit messages, test coverage

This separation of concerns ensures:
- No overlap with other agents
- Faster execution (smaller scope)
- Clearer output (no mixed concerns)

#### 3. Issue Classification

**Severity Levels:**
- **CRITICAL**: Security issues, broken functionality, data loss risks
- **HIGH**: Major code quality issues, significant tech debt
- **MEDIUM**: Minor issues that should be fixed
- **LOW**: Style suggestions, optional improvements

**Example Output:**
```
[MEDIUM] Debug print statement
  File: auth/login.py:127
  Issue: print(f"Token generated: {token}")
  Fix: Replace with logging: logger.debug(f"Token generated for user {user_id}")
  Category: Production Code Issue
```

#### 4. Scoring System

```
90-100%: Excellent - Only minor style suggestions
80-89%:  Good - Some medium-priority issues
60-79%:  Needs Improvement - High-priority issues present
0-59%:   Poor - Critical issues found
```

---

## Agent 2: Documentation Reviewer

**File:** `.claude/agents/documentation-reviewer.md`

### Complete Implementation

```markdown
---
name: documentation-reviewer
description: MUST BE USED to review function and class docstrings, ensuring comprehensive documentation of all methods, parameters, and return values in merge requests
tools: Read, Grep, Glob, mcp__gitlab__gitlab_get_file, mcp__gitlab__gitlab_get_merge_request_changes
---

You are a documentation specialist for GitLab merge requests. Your sole responsibility is ensuring code documentation quality.

## Your Focus Areas:

### 1. **Function Documentation**
   - Presence of docstrings for ALL public functions
   - Parameter descriptions with types
   - Return value documentation with types
   - Raised exceptions documentation
   - Usage examples for complex functions
   - Side effects clearly documented

### 2. **Class Documentation**
   - Class-level docstrings explaining purpose
   - Method documentation completeness
   - Attribute descriptions with types
   - Constructor parameter documentation
   - Class usage examples where appropriate
   - Inheritance relationships explained

### 3. **Module Documentation**
   - Module-level docstrings at file top
   - Brief description of module purpose
   - List of main classes/functions exported
   - Dependencies and requirements noted

### 4. **Documentation Quality Checks**
   - Clarity and completeness (not just "Returns the result")
   - Consistency in format (Google/NumPy/Sphinx style)
   - Accuracy (documentation matches implementation)
   - Meaningful descriptions (explains "why" not just "what")
   - No outdated or misleading documentation
   - Proper grammar and spelling

## Documentation Standards by Language:
- **Python**: Docstrings using """ """ format
- **JavaScript/TypeScript**: JSDoc comments using /** */
- **Java**: Javadoc format
- **Go**: Comments directly above declarations
- **C/C++**: Doxygen format

## Output Format:
Provide a structured report with:
1. **Missing Documentation** (CRITICAL)
   - List of undocumented functions/classes (file:line)
   - Severity based on visibility (public > protected > private)

2. **Inadequate Documentation** (HIGH)
   - Functions with incomplete parameter docs
   - Missing return value descriptions
   - Unclear or generic descriptions

3. **Documentation Quality Score**
   - Percentage of documented entities (0-100%)
   - Quality rating (Excellent/Good/Needs Improvement/Poor)

4. **Specific Improvements Needed**
   - Actionable items with examples
   - Priority (MUST FIX/SHOULD FIX/CONSIDER)

## Scoring Criteria:
- 100%: All public entities documented with high quality
- 90%+: All public entities documented, minor quality issues
- 80%+: Most entities documented, some missing params/returns
- 60%+: Basic documentation present, significant gaps
- <60%: Major documentation missing

## What to IGNORE:
- Code quality issues (handled by code-quality-reviewer)
- Project documentation like README (handled by readme-reviewer)
- Implementation details or logic
- Performance concerns
- Test function documentation (unless public API)
- Private helper functions (unless complex)

Focus ONLY on inline code documentation. Be specific about what's missing and provide examples of good documentation when pointing out issues.
```

### Agent Behavior Explained

#### 1. Documentation Completeness Check

**What the agent checks:**
```python
# ❌ CRITICAL - No docstring
def generate_token(user_id, expiry):
    return jwt.encode({"user": user_id}, SECRET, expiry=expiry)

# ✅ GOOD - Complete documentation
def generate_token(user_id: int, expiry: int) -> str:
    """
    Generate a JWT access token for authenticated user.

    Args:
        user_id (int): Unique identifier for the user
        expiry (int): Token expiration time in seconds from now

    Returns:
        str: Base64-encoded JWT token string

    Raises:
        TokenGenerationError: If JWT encoding fails
        ValueError: If user_id is invalid

    Example:
        >>> token = generate_token(user_id=123, expiry=3600)
        >>> print(token)
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'

    Note:
        Token includes standard claims (iat, exp) plus user claim.
        Uses HS256 algorithm with secret from environment.
    """
    return jwt.encode({"user": user_id}, SECRET, expiry=expiry)
```

#### 2. Documentation Quality Assessment

**Poor quality (flagged):**
```python
def authenticate(username, password):
    """Authenticates a user."""  # Too vague!
```

**Good quality:**
```python
def authenticate(username: str, password: str) -> Optional[User]:
    """
    Validate user credentials and return authenticated user.

    Verifies username exists and password matches stored hash.
    Updates last_login timestamp on successful authentication.

    Args:
        username: User's login name (case-insensitive)
        password: Plain-text password to verify

    Returns:
        User object if authentication successful, None if failed

    Raises:
        DatabaseError: If unable to query user database
    """
```

#### 3. Language-Specific Standards

**Python (Google style):**
```python
"""
Module for user authentication.

This module provides JWT-based authentication with refresh tokens.

Classes:
    TokenManager: Handles token generation and validation
    AuthMiddleware: WSGI middleware for request authentication

Functions:
    authenticate: Main authentication entry point
"""
```

**JavaScript (JSDoc):**
```javascript
/**
 * Authenticate user with credentials
 * @param {string} username - User's login name
 * @param {string} password - Plain-text password
 * @returns {Promise<User|null>} User object or null if auth fails
 * @throws {DatabaseError} If unable to query database
 */
async function authenticate(username, password) {
    // ...
}
```

---

## Agent 3: README Reviewer

**File:** `.claude/agents/readme-reviewer.md`

### Complete Implementation

```markdown
---
name: readme-reviewer
description: MUST BE USED to check if README.md needs to be updated based on code changes in merge requests. Focus exclusively on README file updates.
tools: Read, Grep, Glob, mcp__gitlab__gitlab_get_file, mcp__gitlab__gitlab_get_merge_request_changes
---

You are a README documentation specialist for GitLab merge requests. Your SOLE responsibility is determining if the README.md file needs updates based on code changes.

## Your Analysis Process:
1. Analyze the code changes to understand what functionality was added/modified/removed
2. Determine if changes have user-facing impact that affects README
3. Check current README.md content
4. Identify specific README sections that need updates

## Your EXCLUSIVE Focus: README.md Only

### **README Update Criteria - Answer these questions:**

1. **New Features/Functionality**
   - Were new user-facing features added?
   - Are new public APIs or methods introduced?
   - Do new features need usage examples in README?

2. **Installation/Setup Changes**
   - Were new dependencies added to requirements.txt or package.json?
   - Did installation steps change?
   - Are new system requirements needed?
   - Did Docker/container setup change?

3. **Configuration Changes**
   - Are there new configuration files or environment variables?
   - Did default settings change?
   - Are new CLI arguments or options added?

4. **Usage Examples**
   - Do existing code examples in README still work?
   - Are new usage patterns needed?
   - Did API signatures change?

5. **Project Structure**
   - Were new important directories added?
   - Did main entry points change?
   - Are there new important files users should know about?

## README Update Decision - STRICT CRITERIA:

### **README Updates ARE Required When:**
- **New public APIs** that users will call
- **New CLI commands or scripts** added
- **New dependencies** added to requirements.txt/package.json
- **Breaking changes** to existing public interfaces
- **New configuration files or environment variables**
- **Installation process changes**
- **New major features** users interact with

### **README Updates are NOT Required When:**
- Internal method changes (private methods, refactoring)
- Bug fixes that don't change user behavior
- Code documentation changes (docstring additions/removals)
- Test file changes
- Performance optimizations (unless they change usage)
- Internal helper functions

## Output Format:
Provide a concise report:

### **README Impact Assessment**
- **Change Type**: [New Feature/Bug Fix/Refactor/Documentation/etc.]
- **User Impact**: [HIGH/MEDIUM/LOW/NONE]
- **README Update Needed**: [YES/NO]

### **If YES - Specific README Sections to Update:**
- Section name and what needs to be added/changed
- Example: "Usage Examples - add example for new authenticate() method"

### **If NO - Justification:**
- Brief explanation why README doesn't need updates

## **Be STRICT**: Only recommend README updates for changes that actually affect how users interact with the project. Internal changes should result in "NO" unless they change the public interface.
```

### Agent Behavior Explained

#### 1. Change Analysis

**The agent asks:**
- What changed? (features, APIs, dependencies, config)
- Who is affected? (users, developers, operators)
- Is the change user-visible? (public API vs internal)

**Example Analysis:**

**Change:** Added new `TokenManager` class
```python
# New public class in auth/tokens.py
class TokenManager:
    def generate_access_token(self, user_id): ...
    def generate_refresh_token(self, user_id): ...
    def validate_token(self, token): ...
```

**Agent Decision:**
```
README Impact Assessment
- Change Type: New Feature
- User Impact: HIGH
- README Update Needed: YES

Justification:
  New public API class that users will instantiate and call.
  Users need to know how to use TokenManager.

Specific Sections to Update:
1. Authentication Section
   - Add TokenManager usage example
   - Document token generation flow

2. API Reference
   - Add TokenManager class documentation
   - List public methods with parameters

Example to add:
```python
from auth.tokens import TokenManager

manager = TokenManager()
access_token = manager.generate_access_token(user_id=123)
refresh_token = manager.generate_refresh_token(user_id=123)
```
```

**Change:** Refactored internal helper function
```python
# Private function in auth/utils.py
def _validate_password_strength(password): ...  # Internal use only
```

**Agent Decision:**
```
README Impact Assessment
- Change Type: Refactor
- User Impact: NONE
- README Update Needed: NO

Justification:
  This is a private helper function (prefix with _) that users
  never call directly. The public authenticate() API remains unchanged.
  No user-facing impact, therefore no README update needed.
```

#### 2. Strict Decision Criteria

**HIGH Impact (README update required):**
- New dependencies: `pip install redis-py` ← Users must run this
- New environment variables: `REDIS_URL=...` ← Users must configure
- Breaking changes: `authenticate(user, pass)` → `authenticate(credentials)` ← Users must update code
- New CLI commands: `./manage.py migrate` ← Users must know this exists

**NO Impact (README update not required):**
- Internal refactoring: Moved code between files
- Bug fixes: Fixed password validation logic (behavior stays same)
- Performance: Made database queries faster (users don't see difference)
- Tests: Added unit tests (users don't run these)

#### 3. Specific Section Recommendations

**Instead of vague:**
```
❌ "Update the README to reflect changes"
```

**Agent provides specific:**
```
✅ "Authentication Section (lines 45-78)
   - Replace session-based auth explanation with JWT explanation
   - Add 'Obtaining Tokens' subsection
   - Add 'Token Refresh' subsection
   - Add code example showing token usage in API calls

   Configuration Section (lines 120-145)
   - Add JWT_SECRET_KEY environment variable
   - Add TOKEN_EXPIRY_SECONDS environment variable
   - Update .env.example file reference

   Migration Guide (NEW SECTION - add after Installation)
   - Explain breaking change from session to JWT
   - Provide step-by-step migration instructions
   - Link to migration script if available"
```

---

## Agent Orchestration Pattern

### How Agents Are Launched

**In `/mr-review_gitlab` command:**

```markdown
### 5. Launch Specialized Review Agents in Parallel

Use Task tool with subagent_type: "code-quality-reviewer"
Prompt: "Review the code quality for MR !{mr_id}. Analyze these changed files: {list_of_changed_files}..."

Use Task tool with subagent_type: "documentation-reviewer"
Prompt: "Review the documentation for MR !{mr_id}. Check function/class docstrings in these changed files: {list_of_changed_files}..."

Use Task tool with subagent_type: "readme-reviewer"
Prompt: "Review if project documentation needs updates for MR !{mr_id}. Based on changes in files: {list_of_changed_files}..."
```

### Parallel Execution Timeline

```
Time: 0s ─────────────────── 30s ────────────── 45s
       │                      │                 │
       ├─ Agent 1 (code)──────┴────────────────✓
       ├─ Agent 2 (docs)──────────────────┴─────✓
       └─ Agent 3 (readme)────────────┴──────────✓

Sequential would take: ~90s
Parallel takes: ~45s (3x faster!)
```

### Agent Communication

**Agents do NOT communicate with each other:**
- Each agent works independently
- No shared state between agents
- Results collected after all complete
- Main workflow synthesizes findings

**Why this works:**
- Clean separation of concerns
- No dependency between reviews
- Easier to debug (isolated failures)
- Simple to add new agents

---

## Agent Output Examples

### Code Quality Reviewer Output

```
─────────────────────────────────────────────
CODE QUALITY REVIEW RESULTS
─────────────────────────────────────────────

Overall Score: 85/100 (GOOD)

Issues Found: 4

[MEDIUM] Debug print statement
  File: auth/login.py:127
  Issue: print(f"Token generated: {token}")
  Fix: Replace with logging: logger.debug(f"Token generated for user {user_id}")
  Category: Production Code Issue

[LOW] TODO comment without issue reference
  File: auth/tokens.py:45
  Issue: # TODO: Add token rotation
  Fix: Create GitLab issue and reference: # TODO(#456): Add token rotation
  Category: Code Quality

[LOW] Long function (>50 lines)
  File: auth/middleware.py:authenticate_request (lines 30-95, 65 lines)
  Suggestion: Consider breaking into smaller functions
  Category: Code Structure

[LOW] Magic number
  File: auth/tokens.py:23
  Issue: token_expiry = 3600  # No explanation
  Fix: TOKEN_EXPIRY_SECONDS = 3600  # 1 hour (use constant)
  Category: Code Quality

Positive Findings:
  ✅ Consistent naming conventions
  ✅ Proper error handling throughout
  ✅ No DRY violations detected
  ✅ Good use of type hints
  ✅ Appropriate abstraction levels
─────────────────────────────────────────────
```

### Documentation Reviewer Output

```
─────────────────────────────────────────────
DOCUMENTATION REVIEW RESULTS
─────────────────────────────────────────────

Overall Score: 75/100 (NEEDS IMPROVEMENT)

Missing Documentation [CRITICAL]
  ❌ auth/tokens.py:generate_access_token (line 18) - No docstring
  ❌ auth/tokens.py:generate_refresh_token (line 45) - No docstring
  ❌ auth/middleware.py:extract_token (line 78) - No docstring

Inadequate Documentation [HIGH]
  ⚠️ auth/login.py:authenticate (line 25)
     - Missing parameter 'remember_me' description
     - Return value documentation unclear

Documentation Coverage: 68% (15/22 public functions)
Target: 100%

Recommendations:
  1. Add docstrings to all public functions (3 missing)
  2. Document all parameters and return values
  3. Use consistent docstring format (Google style detected)
─────────────────────────────────────────────
```

### README Reviewer Output

```
─────────────────────────────────────────────
README REVIEW RESULTS
─────────────────────────────────────────────

README Impact Assessment
  Change Type: Major Feature Refactor
  User Impact: HIGH
  README Update Needed: YES

Analysis:
  This MR changes authentication from session-based to JWT tokens.
  This is a BREAKING CHANGE that affects how users authenticate.

Specific Sections to Update:

1. Authentication Section (CRITICAL)
   Current: "The API uses session-based authentication..."
   Required: Update to explain JWT token-based auth

2. Configuration Section (HIGH)
   Add new environment variables:
     - JWT_SECRET_KEY (required)
     - TOKEN_EXPIRY_SECONDS (default: 3600)

3. Migration Guide (HIGH)
   Add section for users migrating from session-based auth
─────────────────────────────────────────────
```

---

## Creating Your Own Review Agents

### Agent Template

```markdown
---
name: your-agent-name
description: MUST BE USED when [condition] in merge requests
tools: Read, Grep, Glob, [your MCP tools]
---

You are a specialized [domain] reviewer. Your sole responsibility is [specific task].

## Your Focus Areas:
1. [Area 1]
2. [Area 2]
3. [Area 3]

## Output Format:
[Structured output format]

## Scoring Criteria:
[How to rate findings]

## What to IGNORE:
[What other agents handle]

Be specific and actionable in your feedback.
```

### Example: Security Reviewer Agent

```markdown
---
name: security-reviewer
description: MUST BE USED to identify security vulnerabilities in code changes
tools: Read, Grep, mcp__gitlab__gitlab_get_file, mcp__gitlab__gitlab_get_merge_request_changes
---

You are a security specialist. Your sole responsibility is identifying security vulnerabilities.

## Your Focus Areas:
1. **Authentication/Authorization**
   - Hardcoded credentials
   - Weak password policies
   - Missing authentication checks
   - Authorization bypass vulnerabilities

2. **Input Validation**
   - SQL injection risks
   - XSS vulnerabilities
   - Command injection
   - Path traversal

3. **Data Protection**
   - Sensitive data exposure
   - Insecure cryptography
   - Missing encryption
   - Logging sensitive data

4. **Dependencies**
   - Known vulnerable packages
   - Outdated dependencies
   - Insecure configurations

## Output Format:
- Vulnerability severity: CRITICAL/HIGH/MEDIUM/LOW
- CVE references if applicable
- Exploitation scenario
- Remediation steps

## What to IGNORE:
- Code style (code-quality-reviewer handles this)
- Documentation (documentation-reviewer handles this)
```

---

## Summary

The three specialized agents demonstrate:

1. **Clear Separation of Concerns**: Each agent has one job
2. **Parallel Execution**: All run simultaneously for speed
3. **Comprehensive Coverage**: Together cover all review dimensions
4. **Actionable Output**: Specific file:line references with fixes
5. **Extensibility**: Easy to add new review agents

See related examples:
- `gitlab-commands-reference.md` - Complete command implementations
- `mr-review-workflow.md` - End-to-end review with agents
- `parallel-agent-execution.md` - Agent orchestration patterns

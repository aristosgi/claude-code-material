# Merge Request Review Workflow - End-to-End Example

This example demonstrates the complete `/mr-review_gitlab` workflow, showing how GitLab MCP tools and specialized agents work together to provide comprehensive MR reviews.

## Scenario

**Project:** Authentication Service Refactor
**MR:** !423 - Refactor user authentication module
**Author:** john.doe
**Branch:** `feature/auth-refactor` → `main`
**Files Changed:** 8 files (auth/, tests/, README.md)

## Command Execution

```bash
User: /mr-review_gitlab 423
```

## Workflow Execution Timeline

### Stage 1: Parse Arguments & Initialize (0-2s)

```
📋 Starting MR Review Workflow
Arguments parsed:
  MR ID: 423
  Flags: None
  Config: .claude/.mr-requirements.md (default)

Creating TODO list to track progress...
✅ TODO list created with 8 items
```

**TODO List Created:**
```
- [in_progress] Parse arguments and setup
- [pending] Get MR information from GitLab API
- [pending] Analyze changed files
- [pending] Load requirements configuration
- [pending] Launch specialized review agents
- [pending] Synthesize results from all agents
- [pending] Generate unified review report
- [pending] Present interactive action options
```

### Stage 2: Get MR Information (2-5s)

```
[1/8] Getting MR information...

Using MCP tool: mcp__gitlab__gitlab_get_merge_request(mr_iid=423)

Response received:
{
  "iid": 423,
  "title": "Refactor user authentication module",
  "description": "Replaces session-based auth with JWT tokens...",
  "state": "opened",
  "author": {"username": "john.doe"},
  "source_branch": "feature/auth-refactor",
  "target_branch": "main",
  "created_at": "2025-01-14T10:30:00Z",
  "updated_at": "2025-01-15T08:15:00Z"
}

Using MCP tool: mcp__gitlab__gitlab_get_merge_request_changes(mr_iid=423)

Response received: 8 files changed, 450 additions, 120 deletions

✅ MR information retrieved
```

**Display Summary:**
```
────────────────────────────────────────────────────────────
📋 MR !423: Refactor user authentication module
────────────────────────────────────────────────────────────
🔀 feature/auth-refactor → main
👤 Author: john.doe
📅 Created: 2025-01-14 (1 day ago)
📊 Status: opened
📝 Description:
    Replaces session-based auth with JWT tokens.
    Adds refresh token support and improves security.

📂 Files Changed (8):
  ✏️  auth/login.py (+85, -45)
  ✏️  auth/tokens.py (+120, -0) [NEW]
  ✏️  auth/middleware.py (+60, -30)
  ✏️  auth/utils.py (+40, -15)
  ✏️  tests/test_auth.py (+100, -20)
  ✏️  tests/test_tokens.py (+30, -0) [NEW]
  ✏️  requirements.txt (+10, -2)
  ✏️  README.md (+5, -8)
────────────────────────────────────────────────────────────
```

### Stage 3: Analyze Changed Files (5-10s)

```
[2/8] Analyzing changed files...

Fetching file content for each changed file...

File 1/8: auth/login.py
  → mcp__gitlab__gitlab_get_file(file_path="auth/login.py", ref="feature/auth-refactor")
  ✅ Retrieved (320 lines)

File 2/8: auth/tokens.py [NEW]
  → mcp__gitlab__gitlab_get_file(file_path="auth/tokens.py", ref="feature/auth-refactor")
  ✅ Retrieved (180 lines)

File 3/8: auth/middleware.py
  → mcp__gitlab__gitlab_get_file(file_path="auth/middleware.py", ref="feature/auth-refactor")
  ✅ Retrieved (150 lines)

... (continuing for remaining 5 files)

✅ All changed files analyzed (8/8)
```

### Stage 4: Load Requirements (10-11s)

```
[3/8] Loading review requirements...

Reading: .claude/.mr-requirements.md

Requirements loaded:
  ✅ Code Quality Standards
  ✅ Documentation Requirements
  ✅ Security Checks
  ✅ Testing Standards
  ✅ Git Commit Standards
  ✅ README Update Guidelines
```

### Stage 5: Launch Specialized Agents in PARALLEL (11-45s)

```
[4/8] Launching specialized review agents...

🚀 Launching 3 agents in parallel...

Agent 1: code-quality-reviewer
  Focus: Coding standards, production code issues, best practices
  Files: All 8 changed files
  Status: 🔄 Running...

Agent 2: documentation-reviewer
  Focus: Function/class docstrings, parameter docs, completeness
  Files: auth/*.py files (4 files)
  Status: 🔄 Running...

Agent 3: readme-reviewer
  Focus: README update requirements based on changes
  Files: All changed files + README.md
  Status: 🔄 Running...

Performing manual checks while agents run...
  ✅ Commit message format checked (3 commits)
  ✅ Branch naming convention validated
  ✅ Security scan initiated
```

**Agent 1 Output (code-quality-reviewer):**
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

**Agent 2 Output (documentation-reviewer):**
```
─────────────────────────────────────────────
DOCUMENTATION REVIEW RESULTS
─────────────────────────────────────────────

Overall Score: 75/100 (NEEDS IMPROVEMENT)

Quality Rating: Needs Improvement

Missing Documentation [CRITICAL]
  ❌ auth/tokens.py:generate_access_token (line 18) - No docstring
  ❌ auth/tokens.py:generate_refresh_token (line 45) - No docstring
  ❌ auth/middleware.py:extract_token (line 78) - No docstring

Inadequate Documentation [HIGH]
  ⚠️ auth/login.py:authenticate (line 25)
     - Missing parameter 'remember_me' description
     - Return value documentation unclear

  ⚠️ auth/tokens.py:TokenManager (line 10)
     - Class docstring missing usage example
     - Constructor parameters not documented

Well Documented:
  ✅ auth/login.py:validate_credentials - Excellent docstring
  ✅ auth/utils.py:hash_password - Complete parameter docs
  ✅ tests/test_auth.py - Test functions properly documented

Recommendations:
  1. Add docstrings to all public functions (3 missing)
  2. Document all parameters and return values
  3. Add usage examples for TokenManager class
  4. Use consistent docstring format (Google style detected)

Documentation Coverage: 68% (15/22 public functions)
Target: 100%
─────────────────────────────────────────────
```

**Agent 3 Output (readme-reviewer):**
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

Current README Status:
  ✅ Authentication section exists (lines 45-78)
  ❌ Still describes session-based auth (outdated)
  ❌ No mention of JWT tokens or refresh tokens
  ✅ Installation section up to date
  ⚠️ Configuration section needs JWT secret key documentation

Specific Sections to Update:

1. Authentication Section (CRITICAL)
   Current: "The API uses session-based authentication..."
   Required: Update to explain JWT token-based auth
   Add:
     - How to obtain access tokens
     - Token refresh mechanism
     - Token expiration (1 hour)
     - Example authentication requests

2. Configuration Section (HIGH)
   Add new environment variables:
     - JWT_SECRET_KEY (required)
     - JWT_ALGORITHM (default: HS256)
     - TOKEN_EXPIRY_SECONDS (default: 3600)

3. Installation Section (MEDIUM)
   New dependency added: PyJWT
   Verify requirements.txt is mentioned

4. Migration Guide (HIGH)
   Add section for users migrating from session-based auth:
     - Breaking changes
     - Migration steps
     - Backward compatibility notes

Example sections provided in review notes.
─────────────────────────────────────────────
```

### Stage 6: Manual Security & Git Checks (Concurrent with agents)

```
Performing manual security and git standards checks...

Security Scan Results:
  ✅ No hardcoded secrets detected
  ✅ No SQL injection vulnerabilities
  ✅ Proper use of cryptographic functions (bcrypt)
  ⚠️ JWT secret key loaded from environment (GOOD)
  ✅ Token validation properly implemented

Git Standards Check:
  Commits analyzed: 3

  ✅ Commit 1: "feat: Add JWT token generation module"
     Format: Conventional Commits ✅
     Length: 41 chars (optimal)

  ✅ Commit 2: "refactor: Update login to use JWT tokens"
     Format: Conventional Commits ✅
     Length: 44 chars (optimal)

  ✅ Commit 3: "docs: Update README for JWT authentication"
     Format: Conventional Commits ✅
     Length: 47 chars (optimal)

Branch Naming:
  ✅ "feature/auth-refactor" follows convention (type/description)
```

### Stage 7: Synthesize Results (45-48s)

```
[5/8] Synthesizing results from all agents...

Collecting findings:
  ✅ Code Quality Review: 4 issues (0 critical, 0 high, 1 medium, 3 low)
  ✅ Documentation Review: 5 issues (3 critical, 2 high)
  ✅ README Review: UPDATE REQUIRED
  ✅ Manual Security Check: 1 warning
  ✅ Git Standards: PASS

Aggregating issues by priority...
Generating recommendations...
```

### Stage 8: Generate Unified Report (48-50s)

```
[6/8] Generating unified review report...

═══════════════════════════════════════════════════════════════════
                    MR REVIEW REPORT - !423
               Refactor user authentication module
═══════════════════════════════════════════════════════════════════

OVERALL STATUS: ⚠️ NEEDS WORK
OVERALL SCORE: 78/100

────────────────────────────────────────────────────────────────────
SUMMARY BY REVIEW DIMENSION
────────────────────────────────────────────────────────────────────

✅ Code Quality: 85/100 (GOOD)
  - 4 issues found (1 medium, 3 low)
  - Strong code structure and practices
  - Minor improvements needed

⚠️ Documentation: 75/100 (NEEDS IMPROVEMENT)
  - 5 issues found (3 critical, 2 high)
  - 3 functions missing docstrings
  - Documentation coverage: 68% (target: 100%)

⚠️ README Updates: REQUIRED
  - Breaking change requires documentation
  - 4 sections need updates
  - Migration guide needed

✅ Security: PASS (1 warning)
  - No critical security issues
  - Good security practices
  - JWT secret properly handled

✅ Git Standards: PASS
  - Conventional Commits format ✅
  - Appropriate branch naming ✅
  - 3 well-formatted commits ✅

────────────────────────────────────────────────────────────────────
AGGREGATED ISSUES (Priority Order)
────────────────────────────────────────────────────────────────────

🔴 CRITICAL ISSUES (3) - MUST FIX BEFORE MERGE

  1. Missing docstring: auth/tokens.py:generate_access_token
     Line: 18
     Action: Add comprehensive docstring with params, returns, examples
     Agent: documentation-reviewer

  2. Missing docstring: auth/tokens.py:generate_refresh_token
     Line: 45
     Action: Add comprehensive docstring
     Agent: documentation-reviewer

  3. Missing docstring: auth/middleware.py:extract_token
     Line: 78
     Action: Add docstring explaining token extraction logic
     Agent: documentation-reviewer

🟠 HIGH PRIORITY (3) - SHOULD FIX BEFORE MERGE

  4. README - Authentication section outdated
     File: README.md (lines 45-78)
     Action: Update to explain JWT-based authentication
     Agent: readme-reviewer

  5. README - Missing configuration documentation
     File: README.md
     Action: Document JWT_SECRET_KEY and related env vars
     Agent: readme-reviewer

  6. Inadequate documentation: auth/login.py:authenticate
     Line: 25
     Action: Document 'remember_me' parameter and clarify return value
     Agent: documentation-reviewer

🟡 MEDIUM PRIORITY (1) - CONSIDER FIXING

  7. Debug print statement in production code
     File: auth/login.py:127
     Issue: print(f"Token generated: {token}")
     Action: Replace with proper logging: logger.debug(...)
     Agent: code-quality-reviewer

🟢 LOW PRIORITY (3) - OPTIONAL IMPROVEMENTS

  8. TODO without issue reference (auth/tokens.py:45)
  9. Long function - consider refactoring (auth/middleware.py:30-95)
  10. Magic number - use named constant (auth/tokens.py:23)

────────────────────────────────────────────────────────────────────
ACTIONABLE RECOMMENDATIONS
────────────────────────────────────────────────────────────────────

IMMEDIATE ACTIONS (Required before merge approval):

  1. ✍️ Add missing docstrings (3 functions)
     Estimated time: 15 minutes
     Files: auth/tokens.py, auth/middleware.py

  2. 📝 Update README.md
     Estimated time: 30 minutes
     - Update authentication section
     - Add JWT configuration docs
     - Create migration guide

  3. 🔧 Fix print statement → logging
     Estimated time: 2 minutes
     File: auth/login.py:127

RECOMMENDED ACTIONS (Improve quality):

  4. 📋 Create GitLab issues for TODOs
     Link TODO comments to tracking issues

  5. ♻️ Refactor long function
     Break auth/middleware.py:authenticate_request into smaller functions

────────────────────────────────────────────────────────────────────
PRIORITY MATRIX
────────────────────────────────────────────────────────────────────

MUST FIX:
  ❌ 3 critical documentation issues
  ❌ README updates (breaking change)
  ❌ Print statement → logging

SHOULD FIX:
  ⚠️ Inadequate documentation (2 issues)

CAN DEFER:
  💡 TODOs, refactoring suggestions, constants (4 issues)

────────────────────────────────────────────────────────────────────
NEXT STEPS
────────────────────────────────────────────────────────────────────

For the author (john.doe):
  1. Address 3 critical documentation issues
  2. Update README with JWT authentication details
  3. Replace print statement with logging
  4. Optional: Address low-priority improvements

For reviewers:
  1. Verify docstrings are comprehensive
  2. Confirm README accurately reflects new authentication
  3. Test authentication flows manually

═══════════════════════════════════════════════════════════════════
                         END OF REPORT
═══════════════════════════════════════════════════════════════════
```

### Stage 9: Interactive Actions (50s+)

```
[7/8] Presenting interactive action options...

────────────────────────────────────────────────────────────────────
WHAT WOULD YOU LIKE TO DO?
────────────────────────────────────────────────────────────────────

Based on the review results (NEEDS WORK), here are your options:

1. ✍️ Request Changes from Author
   - Post this review as MR comment
   - Author can address issues and update MR
   - Command: /mr-review_gitlab 423 --comment

2. ⏸️ Continue Discussion
   - Keep conversation open for questions
   - Provide guidance on specific issues
   - Author can ask for clarification

3. ✅ Approve (Not Recommended - unresolved critical issues)
   - Approve despite issues (if acceptable)
   - Command: /mr-review_gitlab 423 --approve

4. 🔄 Re-review After Changes
   - Wait for author to update MR
   - Run review again: /mr-review_gitlab 423

Your access level: Maintainer (can approve and merge)

Recommendation: Request changes (Option 1) due to critical issues
────────────────────────────────────────────────────────────────────
```

## User Takes Action

```
User: /mr-review_gitlab 423 --comment
```

**Result:**
```
Posting review as MR comment...

Using MCP tool: mcp__gitlab__gitlab_add_merge_request_note(
  mr_iid=423,
  body="[Review results formatted as markdown...]"
)

✅ Review posted as comment on MR !423

🔗 View on GitLab: https://gitlab.company.com/team/project/-/merge_requests/423

The author (john.doe) will be notified of your review.
```

## After Author Addresses Issues

**2 hours later...**

```
User: "Check if MR !423 has been updated"

Claude: "Let me check the latest changes..."

Using: mcp__gitlab__gitlab_get_merge_request(mr_iid=423)

Response: "MR !423 updated 45 minutes ago"
Changes:
  - 3 commits added
  - README.md updated
  - Documentation added

User: "/mr-review_gitlab 423"

[Full review process repeats...]

RESULT: ✅ PASS (95/100)
  - All critical issues resolved
  - Documentation complete
  - README updated appropriately

User: "/mr-review_gitlab 423 --approve --merge"

✅ MR !423 approved
✅ MR !423 merged into main
✅ Source branch deleted

🎉 Authentication refactor successfully merged!
```

## Key Takeaways

This workflow demonstrates:

1. **MCP Tool Integration**: Seamless use of GitLab API via MCP tools
2. **Parallel Agent Execution**: 3 specialized agents run simultaneously
3. **Comprehensive Review**: Code quality, documentation, README, security, git standards
4. **Unified Reporting**: All findings synthesized into actionable report
5. **Interactive Workflow**: User chooses next actions based on results
6. **End-to-End Automation**: From review to approval to merge

**Workflow Efficiency:**
- Total time: ~50 seconds for complete review
- Agent parallelization: 3x faster than sequential
- Comprehensive coverage: 5 review dimensions
- Actionable output: Specific file:line references with fixes

See related examples:
- `gitlab-mcp-setup-workflow.md` - Setup process
- `parallel-agent-execution.md` - Agent orchestration details
- `custom-mcp-server.md` - Building your own MCP server

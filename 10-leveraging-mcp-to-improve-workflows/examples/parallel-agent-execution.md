# Parallel Agent Execution - Orchestration Patterns

This example demonstrates how to orchestrate multiple specialized agents running in parallel, using the GitLab MR review workflow as a reference implementation.

## Why Parallel Execution?

**Sequential vs Parallel:**

```
Sequential Execution (90s total):
  Agent 1 (30s) ──────────────►
                              Agent 2 (30s) ──────────────►
                                                          Agent 3 (30s) ──────────────►

Parallel Execution (30s total):
  Agent 1 (30s) ──────────────►
  Agent 2 (30s) ──────────────►
  Agent 3 (30s) ──────────────►
```

**Benefits:**
- **3x faster** (in this case)
- **Better resource utilization**
- **Scales linearly** (4 agents = ~same time as 3)
- **Independent failures** (one agent fails, others continue)

## Parallel Execution in Claude Code

### Method: Single Message, Multiple Task Calls

**Key requirement:** All `Task` tool calls must be in a **single message**.

**❌ WRONG - Sequential (separate messages):**
```
Message 1: Task(subagent_type="agent1", ...)
[Wait for agent1 to complete]

Message 2: Task(subagent_type="agent2", ...)
[Wait for agent2 to complete]

Message 3: Task(subagent_type="agent3", ...)
```

**✅ CORRECT - Parallel (single message):**
```
Message 1:
  Task(subagent_type="agent1", ...)
  Task(subagent_type="agent2", ...)
  Task(subagent_type="agent3", ...)
[All three agents run simultaneously]
```

## Implementation in `/mr-review_gitlab`

### Stage 5: Launch Agents in Parallel

From `.claude/commands/mr-review_gitlab.md`:

```markdown
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
```

### How Claude Code Executes This

**Step 1: Parse command markdown**
- Claude Code sees three `Task` calls in sequence
- All three are in the same response message
- Recognizes parallel execution pattern

**Step 2: Launch agents**
```
Spawning agent 1: code-quality-reviewer
  → New isolated Claude Code instance
  → Tools: Read, Grep, Glob, Bash, mcp__gitlab__*
  → Context: MR !423, changed files list

Spawning agent 2: documentation-reviewer
  → New isolated Claude Code instance
  → Tools: Read, Grep, Glob, mcp__gitlab__*
  → Context: MR !423, changed files list

Spawning agent 3: readme-reviewer
  → New isolated Claude Code instance
  → Tools: Read, Grep, Glob, mcp__gitlab__*
  → Context: MR !423, changed files list

All three agents run concurrently!
```

**Step 3: Collect results**
```
Agent 1 completes (28s): Returns code quality report
Agent 2 completes (32s): Returns documentation report
Agent 3 completes (25s): Returns README assessment

Main thread waits for all three, then continues
Total wait time: max(28, 32, 25) = 32 seconds
```

## Agent Independence

### No Shared State

Each agent has:
- **Own isolated environment**
- **Own tool access** (defined in agent frontmatter)
- **Own conversation history**
- **No communication channel** to other agents

**Example:**

**Agent 1 environment:**
```
Context:
  - MR !423 details
  - Changed files: auth/login.py, auth/tokens.py, ...
  - Requirements from .claude/.mr-requirements.md

Available Tools:
  - Read, Grep, Glob, Bash
  - mcp__gitlab__gitlab_get_file
  - mcp__gitlab__gitlab_get_merge_request_changes

Cannot access:
  - Agent 2's findings
  - Agent 3's decisions
  - Main thread's TODO list
```

### Agent Communication Pattern

```
Main Thread                   Agent 1            Agent 2            Agent 3
     │                           │                  │                  │
     ├─ Launch with prompt ─────►│                  │                  │
     ├─ Launch with prompt ──────┼─────────────────►│                  │
     ├─ Launch with prompt ──────┼──────────────────┼─────────────────►│
     │                           │                  │                  │
     │                           │ (working...)     │ (working...)     │ (working...)
     │                           │                  │                  │
     │◄─ Result ─────────────────┤                  │                  │
     │◄─ Result ─────────────────┼──────────────────┤                  │
     │◄─ Result ─────────────────┼──────────────────┼──────────────────┤
     │                           │                  │                  │
     ├─ Synthesize results       │                  │                  │
     └─ Generate report          │                  │                  │
```

Agents **never** communicate with each other. Main thread:
1. Launches all agents with context
2. Waits for all to complete
3. Collects results
4. Synthesizes findings

## Agent Orchestration Patterns

### Pattern 1: Parallel Analysis (Used in MR Review)

**Use case:** Multiple independent analyses of the same data

**Structure:**
```
Data → Agent 1 (Code Quality) ──►┐
    → Agent 2 (Documentation) ───►├─ Synthesize ─► Unified Report
    → Agent 3 (README) ──────────►┘
```

**Example prompts:**
```
Agent 1: "Analyze code quality in files: [list]"
Agent 2: "Check documentation in files: [list]"
Agent 3: "Determine if README needs updates based on changes in files: [list]"
```

**When to use:**
- Multiple review dimensions
- Each dimension is independent
- All agents analyze same input data
- Results combined at the end

### Pattern 2: Divide and Conquer

**Use case:** Split large task across multiple agents

**Structure:**
```
Large Task → Agent 1 (Files 1-10) ──►┐
          → Agent 2 (Files 11-20) ───►├─ Combine ─► Complete Result
          → Agent 3 (Files 21-30) ───►┘
```

**Example:**
```
# Reviewing 30 files - split into 3 batches
Agent 1: "Review code quality in files: auth/*.py"
Agent 2: "Review code quality in files: api/*.py"
Agent 3: "Review code quality in files: tests/*.py"
```

**When to use:**
- Large dataset to process
- Task is parallelizable
- Order doesn't matter
- Results can be merged

### Pattern 3: Multi-Stage Pipeline

**Use case:** Sequential stages, parallel within each stage

**Structure:**
```
Stage 1 (Parallel):
  Agent A1 → Result A1 ──┐
  Agent A2 → Result A2 ──┤
  Agent A3 → Result A3 ──┴─► Synthesize ─► Input for Stage 2

Stage 2 (Parallel):
  Agent B1 (uses Stage 1 results) ──┐
  Agent B2 (uses Stage 1 results) ──┴─► Final Report
```

**Example:**
```
Stage 1: Analysis
  Agent 1: Extract all functions from changed files
  Agent 2: Extract all classes from changed files
  Agent 3: Extract all imports from changed files

Stage 2: Validation (uses Stage 1 results)
  Agent 4: Check if extracted functions have tests
  Agent 5: Check if extracted classes are documented
```

**When to use:**
- Multi-stage workflow
- Later stages depend on earlier results
- Parallelization within each stage

### Pattern 4: Specialist + Generalist

**Use case:** Specialized agents for specific checks, generalist for overview

**Structure:**
```
Code → Specialist 1 (Security) ──►┐
    → Specialist 2 (Performance) ─►├─ Generalist ─► Prioritized Report
    → Specialist 3 (Compliance) ──►┘   (Synthesizes
                                        & prioritizes)
```

**Example:**
```
Specialist 1: "Find ALL security vulnerabilities (ignore other issues)"
Specialist 2: "Find ALL performance problems (ignore other issues)"
Specialist 3: "Find ALL compliance violations (ignore other issues)"

Generalist: "Given findings from specialists, prioritize and create action plan"
```

**When to use:**
- Deep expertise needed in specific domains
- Need prioritization across domains
- Specialists should be narrow, generalist synthesizes

## Timing and Performance

### Measuring Agent Execution Time

```
Start: 11:30:00
  Launch Agent 1, 2, 3

Agent 3 completes: 11:30:25 (25 seconds)
Agent 1 completes: 11:30:28 (28 seconds)
Agent 2 completes: 11:30:32 (32 seconds)

Total parallel execution time: 32 seconds
Equivalent sequential time: 25 + 28 + 32 = 85 seconds

Speedup: 85 / 32 = 2.66x faster
```

### Optimizing Parallel Execution

**Balance agent workloads:**
```
❌ BAD - Unbalanced:
  Agent 1: 10 files (10s)
  Agent 2: 30 files (60s)
  Agent 3: 5 files (5s)
  Total time: 60s (limited by slowest agent)

✅ GOOD - Balanced:
  Agent 1: 15 files (30s)
  Agent 2: 15 files (30s)
  Agent 3: 15 files (30s)
  Total time: 30s
```

**Limit agent count:**
```
3 agents: 30s (optimal)
6 agents: 32s (diminishing returns, overhead increases)
12 agents: 35s (too much overhead, slower than 3 agents!)
```

**Best practices:**
- 3-5 agents is sweet spot
- Balance workload across agents
- Don't parallelize if task takes <10 seconds
- Consider overhead of spawning agents

## Error Handling in Parallel Execution

### Pattern: Continue on Partial Failure

```
Agent 1: ✅ Completes successfully
Agent 2: ❌ Fails (network error)
Agent 3: ✅ Completes successfully

Main thread:
  ├─ Collect results from Agent 1: ✅
  ├─ Collect results from Agent 2: ❌ Error message
  ├─ Collect results from Agent 3: ✅
  └─ Generate report with:
       - Agent 1 findings
       - Agent 2 error (note the failure)
       - Agent 3 findings
```

**Implementation:**
```markdown
### 6. Synthesize Results from All Agents

Collect findings from all agents:
1. If code-quality-reviewer succeeded: Include findings
   If code-quality-reviewer failed: Note the error
2. If documentation-reviewer succeeded: Include findings
   If documentation-reviewer failed: Note the error
3. If readme-reviewer succeeded: Include findings
   If readme-reviewer failed: Note the error

Generate report with available findings, noting any agent failures.
```

### Pattern: Retry Failed Agents

```
Agent 1: ✅ Success
Agent 2: ❌ Failed (timeout)
Agent 3: ✅ Success

Main thread:
  ├─ Detect Agent 2 failure
  ├─ Retry Agent 2 (attempt 2)
  │    ✅ Success on retry
  └─ Continue with all results
```

## Real-World Example: MR !423 Review

### Timeline

```
00:00 - Parse arguments, create TODO list
00:02 - Get MR details via mcp__gitlab__gitlab_get_merge_request
00:04 - Get MR changes via mcp__gitlab__gitlab_get_merge_request_changes
00:06 - Fetch 8 changed files via mcp__gitlab__gitlab_get_file (parallel)
00:10 - Load requirements from .claude/.mr-requirements.md
00:11 - Launch 3 review agents in parallel:
          Agent 1: code-quality-reviewer
          Agent 2: documentation-reviewer
          Agent 3: readme-reviewer
00:11 - Perform manual checks (git log, security scan) while agents run
00:25 - Agent 3 (readme-reviewer) completes
00:28 - Agent 1 (code-quality-reviewer) completes
00:32 - Agent 2 (documentation-reviewer) completes
00:33 - Synthesize all results
00:35 - Generate unified report
00:36 - Present interactive options

Total time: 36 seconds
(Sequential would have taken: ~70 seconds)
```

### Agent Workloads

**Agent 1 (code-quality-reviewer): 28 seconds**
- Analyzed 8 files (auth/*, tests/*)
- Checked: print statements, TODOs, code structure
- Found: 4 issues (1 medium, 3 low)

**Agent 2 (documentation-reviewer): 32 seconds**
- Analyzed 6 Python files (excluding tests, README)
- Checked: 22 public functions for docstrings
- Found: 5 issues (3 critical, 2 high)

**Agent 3 (readme-reviewer): 25 seconds**
- Analyzed all 8 changed files
- Read current README.md (350 lines)
- Determined: README update required (4 sections)

### Synthesis Process

```
Main Thread (3 seconds):
├─ Collect Agent 1 results:
│    Code quality: 85/100, 4 issues
│
├─ Collect Agent 2 results:
│    Documentation: 75/100, 5 issues
│
├─ Collect Agent 3 results:
│    README update: YES, 4 sections
│
├─ Combine findings:
│    Total issues: 9
│    Overall score: (85 + 75) / 2 = 80/100
│    Status: NEEDS WORK (README + critical docs)
│
└─ Generate unified report:
     - Overall status: NEEDS WORK
     - Priority matrix: 3 critical, 2 high, 1 medium, 3 low
     - Actionable recommendations
     - Interactive options
```

## Advanced Orchestration: Adaptive Parallelism

### Dynamic Agent Selection

**Based on file types:**
```
Changed files detected:
  - 5 Python files → Launch python-reviewer
  - 3 JavaScript files → Launch js-reviewer
  - 2 SQL files → Launch sql-reviewer
  - 1 Dockerfile → Launch docker-reviewer

All 4 agents run in parallel (file-type specific reviews)
```

**Based on change size:**
```
Small MR (<10 files):
  → Single comprehensive reviewer (no need to parallelize)

Medium MR (10-30 files):
  → 3 specialized agents (code, docs, readme)

Large MR (30+ files):
  → 5+ agents (code split by directory, docs, readme, security, performance)
```

### Conditional Agent Execution

```
Analyze MR changes first:
  ├─ If new dependencies detected:
  │    → Launch dependency-security-agent
  │
  ├─ If database migrations detected:
  │    → Launch migration-reviewer-agent
  │
  ├─ If API changes detected:
  │    → Launch api-breaking-changes-agent
  │
  └─ Always launch core agents (code, docs, readme)

All applicable agents run in parallel
```

## Summary

**Key Takeaways:**

1. **Parallel > Sequential**: 2-3x faster for independent tasks
2. **Single Message**: All Task calls must be in one message
3. **Agent Independence**: No shared state, isolated environments
4. **Clear Separation**: Each agent has one specific responsibility
5. **Result Synthesis**: Main thread combines findings
6. **Error Handling**: Continue on partial failure, note errors
7. **Optimal Count**: 3-5 agents balances speed vs overhead

**When to Use Parallel Agents:**
- Multiple independent analyses
- Large dataset to process
- Different review dimensions
- Time-sensitive workflows

**When NOT to Use:**
- Task takes <10 seconds (overhead not worth it)
- Tasks have dependencies (must run sequentially)
- Need agents to communicate (they can't)
- Very simple, single-dimension review

---

See related examples:
- `gitlab-commands-reference.md` - Command implementations
- `gitlab-agents-reference.md` - Agent implementations
- `mr-review-workflow.md` - End-to-end workflow with timing

---
allowed-tools: Read, Write, Glob, Task
argument-hint: [target-path] [--exclude pattern]
description: Generate CLAUDE.md files for repository documentation
---

# Universal Repository Documentation Generator

I'll analyze your codebase and generate comprehensive CLAUDE.md documentation files for each significant directory. This works with any project type: Python, C#, Java, JavaScript/TypeScript, Go, Rust, and more.

## Process

I'll systematically:

1. **Discover project structure** using Glob patterns to find source files across all major languages and frameworks
2. **Identify significant directories** that contain substantial code or configuration
3. **Analyze each directory** to understand its purpose, key files, and dependencies
4. **Generate CLAUDE.md files** with consistent, informative documentation

## File Discovery Patterns

I'll search for files using these patterns to cover all major project types:

**Source Code:**
- `**/*.py` (Python)
- `**/*.js`, `**/*.ts`, `**/*.jsx`, `**/*.tsx` (JavaScript/TypeScript)
- `**/*.cs`, `**/*.csproj`, `**/*.sln` (C#/.NET)
- `**/*.java`, `**/*.kt` (Java/Kotlin)
- `**/*.go` (Go)
- `**/*.rs` (Rust)
- `**/*.cpp`, `**/*.c`, `**/*.h` (C/C++)
- `**/*.php` (PHP)
- `**/*.rb` (Ruby)
- `**/*.swift` (Swift)

**Configuration & Build:**
- `**/package.json`, `**/package-lock.json`, `**/yarn.lock` (Node.js)
- `**/requirements.txt`, `**/pyproject.toml`, `**/setup.py` (Python)
- `**/Cargo.toml` (Rust)
- `**/go.mod`, `**/go.sum` (Go)
- `**/pom.xml`, `**/build.gradle` (Java)
- `**/Gemfile` (Ruby)
- `**/composer.json` (PHP)
- `**/*.config.js`, `**/webpack.config.js`, `**/vite.config.js`
- `**/appsettings.json`, `**/web.config`
- `**/Dockerfile`, `**/*.yml`, `**/*.yaml`

## CLAUDE.md Template

For each directory, I'll create a CLAUDE.md file with this structure:

```markdown
# [Directory Name]

## Purpose
[Clear description of what this directory/module does in the system]

## Key Files
- **filename.ext**: [Purpose and main functionality]
- **config.json**: [What it configures and important settings]

## Dependencies
### Internal
- ../path/to/module (purpose/relationship)

### External
- package-name@version (why it's used here)

## Usage Patterns
[How other parts of the codebase interact with this module]

## Architecture & Design
[Patterns, conventions, and architectural decisions]

## Notes
[Any important context for developers working in this area]
```

## Exclusion Rules

I'll automatically skip these common build/cache directories:
- `node_modules`, `dist`, `build`, `.next`, `out`
- `bin`, `obj`, `target`
- `.git`, `.svn`, `.hg`
- `__pycache__`, `.pytest_cache`, `venv`, `.venv`
- `vendor`, `cache`, `tmp`, `temp`

## Your Task Parameters

- **target-path**: ${1:-.} (defaults to current directory)
- **--exclude**: ${2} (optional additional exclusion pattern)

I'll now analyze your project structure and generate comprehensive documentation for each significant directory.
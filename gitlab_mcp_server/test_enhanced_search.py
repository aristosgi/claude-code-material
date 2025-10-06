#!/usr/bin/env python3
"""
Test script for enhanced GitLab MCP search tools
"""

import asyncio
import json
from gitlab_api import GitLabClient

async def test_search_tools():
    """Test the new search functionality"""
    client = GitLabClient()

    print("🔍 Testing Enhanced GitLab Search Tools")
    print("="*50)

    try:
        # Test 1: File pattern search
        print("\n1. Testing file pattern search...")
        print("● GitLab Search(pattern: '**/test*document_chunker*')")

        files = await client.search_files(client.project_id, "**/test*document_chunker*")
        if files:
            print(f"  ⎿  Found {len(files)} files:")
            for file in files[:3]:  # Show first 3
                print(f"     {file['path']}")
            if len(files) > 3:
                print(f"     ... and {len(files) - 3} more")
        else:
            print("  ⎿  Found 0 files")

        # Test 2: File pattern search for chunk files
        print("\n● GitLab Search(pattern: '**/*test*chunk*')")
        chunk_files = await client.search_files(client.project_id, "**/*test*chunk*")
        if chunk_files:
            print(f"  ⎿  Found {len(chunk_files)} files:")
            for file in chunk_files[:3]:
                print(f"     {file['path']}")
        else:
            print("  ⎿  Found 0 files")

        # Test 3: Search for Python files containing chunker
        print("\n● GitLab Search(pattern: '*chunk*.py')")
        py_files = await client.search_files(client.project_id, "*chunk*.py")
        if py_files:
            print(f"  ⎿  Found {len(py_files)} files:")
            for file in py_files:
                print(f"     {file['path']}")
        else:
            print("  ⎿  Found 0 files")

        # Test 4: Content grep search
        print("\n2. Testing content search...")
        print("● GitLab Grep(pattern: '(password|secret|api[_-]?key)', file_filter: '*.py')")

        matches = await client.grep_repository_content(
            client.project_id,
            r"(password|secret|api[_-]?key)",
            file_filter="*.py",
            case_insensitive=True,
            context_lines=1
        )

        if matches:
            print(f"  ⎿  Found {len(matches)} matches:")
            for match in matches[:3]:  # Show first 3 matches
                print(f"     {match['file']}:{match['line_number']}: {match['line'][:50]}...")
            if len(matches) > 3:
                print(f"     ... and {len(matches) - 3} more matches")
        else:
            print("  ⎿  Found 0 matches")

        # Test 5: Enhanced commit search
        print("\n3. Testing commit search...")
        print("● GitLab Commits(grep: 'document_chunker', limit: 5)")

        commits = await client.search_commits_enhanced(
            client.project_id,
            grep="document_chunker",
            limit=5
        )

        if commits:
            print(f"  ⎿  Found {len(commits)} commits:")
            for commit in commits:
                short_message = commit['message'].split('\n')[0][:60]
                print(f"     {commit['short_id']}: {short_message}")
        else:
            print("  ⎿  Found 0 commits")

        # Test 6: Search commits by author
        print("\n● GitLab Commits(author: 'Aristos', limit: 3)")
        author_commits = await client.search_commits_enhanced(
            client.project_id,
            author="Aristos",
            limit=3
        )

        if author_commits:
            print(f"  ⎿  Found {len(author_commits)} commits:")
            for commit in author_commits:
                short_message = commit['message'].split('\n')[0][:50]
                print(f"     {commit['short_id']}: {short_message}")
        else:
            print("  ⎿  Found 0 commits")

        print("\n✅ Enhanced search tools testing completed!")

    except Exception as e:
        print(f"\n❌ Error testing search tools: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_search_tools())
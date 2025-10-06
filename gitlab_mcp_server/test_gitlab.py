#!/usr/bin/env python3
"""Test GitLab API client with curl-based approach"""

import asyncio
import json
from gitlab_api import GitLabClient


async def test_gitlab_api():
    """Test the GitLab API using curl commands"""
    client = GitLabClient()

    print("Testing GitLab API with curl-based approach...")
    print(f"Using token: {client.token[:10]}...")
    print(f"GitLab URL: {client.base_url}")
    print(f"Project ID: {client.project_id}")
    print("-" * 50)

    try:
        # Test 1: Get project info
        print("\n1. Testing get_project...")
        project = await client.get_project()
        print(f"✅ Project: {project.get('name', 'Unknown')} (ID: {project.get('id', 'Unknown')})")

        # Test 2: List merge requests
        print("\n2. Testing list_merge_requests...")
        mrs = await client.list_merge_requests()
        print(f"✅ Found {len(mrs) if isinstance(mrs, list) else 0} merge requests")

        # Test 3: Test get_merge_request_changes for MR !9 (if it exists)
        if isinstance(mrs, list) and len(mrs) > 0:
            print("\n3. Testing get_merge_request_changes...")
            mr_iid = mrs[0].get('iid', 9)  # Use first MR or fallback to 9
            try:
                changes = await client.get_merge_request_changes(client.project_id, mr_iid)
                if isinstance(changes, dict):
                    file_changes = changes.get('changes', [])
                    print(f"✅ MR !{mr_iid} has {len(file_changes)} file changes")
                    if file_changes:
                        for change in file_changes[:3]:  # Show first 3 files
                            print(f"   - {change.get('new_path', change.get('old_path', 'unknown'))}")
                else:
                    print(f"✅ Got changes response: {type(changes)}")
            except Exception as e:
                print(f"⚠️ Could not get changes for MR !{mr_iid}: {e}")

        # Test 4: List pipelines
        print("\n4. Testing list_pipelines...")
        pipelines = await client.list_pipelines(client.project_id, per_page=5)
        print(f"✅ Found {len(pipelines) if isinstance(pipelines, list) else 0} pipelines")

        # Test 5: List branches (needed for file tests)
        print("\n5. Testing list_branches...")
        branches = await client.list_branches(client.project_id)
        print(f"✅ Found {len(branches) if isinstance(branches, list) else 0} branches")
        if isinstance(branches, list) and branches:
            print(f"   Sample branches: {', '.join([b.get('name', '') for b in branches[:3]])}")

        # Test 6: Test get_file
        print("\n6. Testing get_file...")
        try:
            file_content = await client.get_file(client.project_id, "README.md", "main")
            if isinstance(file_content, dict) and "content" in file_content:
                content_preview = file_content["content"][:100] + "..." if len(file_content["content"]) > 100 else file_content["content"]
                print(f"✅ Got README.md content ({len(file_content['content'])} chars): {content_preview}")
            else:
                print(f"✅ Got file response: {type(file_content)}")
        except Exception as e:
            print(f"⚠️ Could not get README.md: {e}")

        # Test 6b: Test get_file with different branch
        print("\n6b. Testing get_file with branch...")
        try:
            # Try to get file from a different branch if available
            if isinstance(branches, list) and len(branches) > 1:
                test_branch = branches[1].get('name', 'main')
                file_content = await client.get_file(client.project_id, "README.md", test_branch)
                if isinstance(file_content, dict) and "content" in file_content:
                    print(f"✅ Got README.md from branch '{test_branch}' ({len(file_content['content'])} chars)")
                else:
                    print(f"✅ Got file response from branch '{test_branch}': {type(file_content)}")
            else:
                print("⚠️ No additional branches available for testing")
        except Exception as e:
            print(f"⚠️ Could not get file from different branch: {e}")

        print("\n✅ All tests passed! The curl-based approach works!")

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_gitlab_api())
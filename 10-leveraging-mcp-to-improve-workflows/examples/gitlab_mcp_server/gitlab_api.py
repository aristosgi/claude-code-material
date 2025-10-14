#!/usr/bin/env python3
"""
GitLab API Client using curl-based approach that actually works
Based on the working authentication from .claude/commands
"""

import json
import subprocess
import logging
from typing import Any, Dict, List, Optional
import base64
from urllib.parse import quote
import asyncio

logger = logging.getLogger("gitlab-client")


class GitLabClient:
    """GitLab client using curl commands exactly as in .claude/commands"""

    def __init__(self):
        # Load config from .claude/.gitlab-config
        self.config = self._load_config()
        self.token = self.config.get("GITLAB_TOKEN", "")
        self.base_url = self.config.get("GITLAB_URL", "https://gitlab.swpd")
        self.project_id = self.config.get("PROJECT_ID", "")

    def _load_config(self) -> Dict[str, str]:
        """Load GitLab configuration from .claude/.gitlab-config"""
        config = {}
        try:
            with open(".claude/.gitlab-config", "r") as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        key, value = line.strip().split("=", 1)
                        config[key] = value
        except Exception as e:
            logger.warning(f"Could not load config: {e}, using defaults")
            config = {
                "GITLAB_TOKEN": "",
                "GITLAB_URL": "https://gitlab.swpd",
                "PROJECT_ID": "",
                "PROJECT_NAME": "",
                "PROJECT_PATH": ""
            }
        return config

    async def _make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None, retries: int = 3) -> Any:
        """
        Make a GitLab API request using curl exactly as in the working bash scripts
        Uses -k flag to bypass SSL verification and proper retry logic
        """
        url = f"{self.base_url}{endpoint}"

        for attempt in range(1, retries + 1):
            try:
                # Build curl command exactly as in the working bash scripts
                cmd = [
                    "curl", "-k", "-s",  # -k bypasses SSL, -s for silent
                    "--connect-timeout", "10",
                    "--max-time", "20",
                    "-H", f"Authorization: Bearer {self.token}",
                    "-H", "Content-Type: application/json"
                ]

                if method != "GET":
                    cmd.extend(["-X", method])

                if data:
                    cmd.extend(["-d", json.dumps(data)])

                cmd.append(url)

                # Execute curl command with robust encoding handling for Windows
                try:
                    # Try UTF-8 first (most common)
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, encoding='utf-8')
                except UnicodeDecodeError:
                    # Fall back to binary mode and decode manually
                    result = subprocess.run(cmd, capture_output=True, timeout=30)
                    if result.returncode == 0 and result.stdout:
                        # Try UTF-8, then latin-1 (which never fails), then replace errors
                        try:
                            stdout = result.stdout.decode('utf-8')
                        except UnicodeDecodeError:
                            try:
                                stdout = result.stdout.decode('latin-1')
                            except UnicodeDecodeError:
                                stdout = result.stdout.decode('utf-8', errors='replace')
                        # Create a mock result object
                        class MockResult:
                            def __init__(self, returncode, stdout, stderr):
                                self.returncode = returncode
                                self.stdout = stdout
                                self.stderr = stderr.decode('utf-8', errors='replace') if isinstance(stderr, bytes) else stderr
                        result = MockResult(result.returncode, stdout, result.stderr)

                if result.returncode == 0 and result.stdout:
                    try:
                        return json.loads(result.stdout)
                    except json.JSONDecodeError:
                        # Some endpoints return plain text (like logs)
                        return result.stdout

                logger.warning(f"Attempt {attempt} failed: {result.stderr}")
                if attempt < retries:
                    await asyncio.sleep(2)  # Wait 2 seconds before retry

            except subprocess.TimeoutExpired:
                logger.warning(f"Attempt {attempt} timed out")
                if attempt < retries:
                    await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Request failed: {e}")
                if attempt < retries:
                    await asyncio.sleep(2)

        raise Exception(f"API request failed after {retries} attempts: {endpoint}")

    # Project operations
    async def get_project(self) -> Dict:
        """Get project details"""
        if self.project_id.isdigit():
            endpoint = f"/api/v4/projects/{self.project_id}"
        else:
            # URL-encode the path
            encoded_path = quote(self.project_id, safe='')
            endpoint = f"/api/v4/projects/{encoded_path}"
        return await self._make_request(endpoint)

    # Merge Request operations
    async def list_merge_requests(self, state: str = "opened", scope: str = "all") -> List[Dict]:
        """List merge requests for a project"""
        endpoint = f"/api/v4/projects/{self.project_id}/merge_requests"
        params = f"?state={state}&scope={scope}"
        return await self._make_request(endpoint + params)

    async def get_merge_request(self, project_id: str, mr_iid: int) -> Dict:
        """Get a specific merge request"""
        endpoint = f"/api/v4/projects/{project_id}/merge_requests/{mr_iid}"
        return await self._make_request(endpoint)

    async def create_merge_request(self, project_id: str, source_branch: str, target_branch: str,
                                  title: str, description: str = None, remove_source_branch: bool = False) -> Dict:
        """Create a new merge request"""
        endpoint = f"/api/v4/projects/{project_id}/merge_requests"
        data = {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
            "remove_source_branch_after_merge": remove_source_branch
        }
        if description:
            data["description"] = description
        return await self._make_request(endpoint, method="POST", data=data)

    async def approve_merge_request(self, project_id: str, mr_iid: int) -> Dict:
        """Approve a merge request"""
        endpoint = f"/api/v4/projects/{project_id}/merge_requests/{mr_iid}/approve"
        return await self._make_request(endpoint, method="POST")

    async def merge_merge_request(self, project_id: str, mr_iid: int, merge_commit_message: str = None,
                                  should_remove_source_branch: bool = True,
                                  merge_when_pipeline_succeeds: bool = False) -> Dict:
        """Merge a merge request"""
        endpoint = f"/api/v4/projects/{project_id}/merge_requests/{mr_iid}/merge"
        data = {
            "should_remove_source_branch": should_remove_source_branch,
            "merge_when_pipeline_succeeds": merge_when_pipeline_succeeds
        }
        if merge_commit_message:
            data["merge_commit_message"] = merge_commit_message
        return await self._make_request(endpoint, method="PUT", data=data)

    async def add_merge_request_note(self, project_id: str, mr_iid: int, body: str) -> Dict:
        """Add a comment to a merge request"""
        endpoint = f"/api/v4/projects/{project_id}/merge_requests/{mr_iid}/notes"
        data = {"body": body}
        return await self._make_request(endpoint, method="POST", data=data)

    # Pipeline operations
    async def list_pipelines(self, project_id: str, status: str = None, ref: str = None, per_page: int = 20) -> List[Dict]:
        """List pipelines for a project"""
        endpoint = f"/api/v4/projects/{project_id}/pipelines"
        params = f"?per_page={per_page}"
        if status:
            params += f"&status={status}"
        if ref:
            params += f"&ref={ref}"
        return await self._make_request(endpoint + params)

    async def get_pipeline(self, project_id: str, pipeline_id: int) -> Dict:
        """Get details of a specific pipeline"""
        endpoint = f"/api/v4/projects/{project_id}/pipelines/{pipeline_id}"
        return await self._make_request(endpoint)

    async def trigger_pipeline(self, project_id: str, ref: str, variables: Dict = None) -> Dict:
        """Trigger a new pipeline"""
        endpoint = f"/api/v4/projects/{project_id}/pipeline"
        data = {"ref": ref}
        if variables:
            data["variables"] = [{"key": k, "value": v} for k, v in variables.items()]
        return await self._make_request(endpoint, method="POST", data=data)

    async def retry_pipeline(self, project_id: str, pipeline_id: int) -> Dict:
        """Retry a pipeline"""
        endpoint = f"/api/v4/projects/{project_id}/pipelines/{pipeline_id}/retry"
        return await self._make_request(endpoint, method="POST")

    async def cancel_pipeline(self, project_id: str, pipeline_id: int) -> Dict:
        """Cancel a pipeline"""
        endpoint = f"/api/v4/projects/{project_id}/pipelines/{pipeline_id}/cancel"
        return await self._make_request(endpoint, method="POST")

    # Job operations
    async def list_jobs(self, project_id: str, pipeline_id: int = None, scope: List[str] = None) -> List[Dict]:
        """List jobs for a project or pipeline"""
        if pipeline_id:
            endpoint = f"/api/v4/projects/{project_id}/pipelines/{pipeline_id}/jobs"
        else:
            endpoint = f"/api/v4/projects/{project_id}/jobs"

        if scope:
            scope_param = "&".join([f"scope[]={s}" for s in scope])
            endpoint += f"?{scope_param}"

        return await self._make_request(endpoint)

    async def get_job(self, project_id: str, job_id: int) -> Dict:
        """Get details of a specific job"""
        endpoint = f"/api/v4/projects/{project_id}/jobs/{job_id}"
        return await self._make_request(endpoint)

    async def get_job_log(self, project_id: str, job_id: int) -> str:
        """Get the log of a specific job"""
        endpoint = f"/api/v4/projects/{project_id}/jobs/{job_id}/trace"
        return await self._make_request(endpoint)

    async def retry_job(self, project_id: str, job_id: int) -> Dict:
        """Retry a job"""
        endpoint = f"/api/v4/projects/{project_id}/jobs/{job_id}/retry"
        return await self._make_request(endpoint, method="POST")

    async def cancel_job(self, project_id: str, job_id: int) -> Dict:
        """Cancel a job"""
        endpoint = f"/api/v4/projects/{project_id}/jobs/{job_id}/cancel"
        return await self._make_request(endpoint, method="POST")

    # Issue operations
    async def list_issues(self, project_id: str, state: str = "opened", labels: List[str] = None,
                         milestone: str = None, assignee_username: str = None) -> List[Dict]:
        """List issues for a project"""
        endpoint = f"/api/v4/projects/{project_id}/issues"
        params = f"?state={state}"
        if labels:
            params += f"&labels={','.join(labels)}"
        if milestone:
            params += f"&milestone={milestone}"
        if assignee_username:
            params += f"&assignee_username={assignee_username}"
        return await self._make_request(endpoint + params)

    async def create_issue(self, project_id: str, title: str, description: str = None,
                          labels: List[str] = None, assignee_ids: List[int] = None) -> Dict:
        """Create a new issue"""
        endpoint = f"/api/v4/projects/{project_id}/issues"
        data = {"title": title}
        if description:
            data["description"] = description
        if labels:
            data["labels"] = ",".join(labels)
        if assignee_ids:
            data["assignee_ids"] = assignee_ids
        return await self._make_request(endpoint, method="POST", data=data)

    # Branch operations
    async def list_branches(self, project_id: str, search: str = None) -> List[Dict]:
        """List branches for a project"""
        endpoint = f"/api/v4/projects/{project_id}/repository/branches"
        if search:
            endpoint += f"?search={search}"
        return await self._make_request(endpoint)

    async def create_branch(self, project_id: str, branch: str, ref: str) -> Dict:
        """Create a new branch"""
        endpoint = f"/api/v4/projects/{project_id}/repository/branches"
        data = {"branch": branch, "ref": ref}
        return await self._make_request(endpoint, method="POST", data=data)

    async def delete_branch(self, project_id: str, branch: str) -> None:
        """Delete a branch"""
        endpoint = f"/api/v4/projects/{project_id}/repository/branches/{quote(branch, safe='')}"
        return await self._make_request(endpoint, method="DELETE")

    # File operations
    async def get_file(self, project_id: str, file_path: str, ref: str = "main") -> Dict:
        """Get file content from repository"""
        encoded_path = quote(file_path, safe='')
        endpoint = f"/api/v4/projects/{project_id}/repository/files/{encoded_path}?ref={ref}"
        result = await self._make_request(endpoint)
        # Decode base64 content if present
        if isinstance(result, dict) and "content" in result:
            result["content"] = base64.b64decode(result["content"]).decode('utf-8')
        return result

    async def create_or_update_file(self, project_id: str, file_path: str, content: str,
                                    branch: str, commit_message: str, create: bool = True) -> Dict:
        """Create or update a file in the repository"""
        encoded_path = quote(file_path, safe='')
        endpoint = f"/api/v4/projects/{project_id}/repository/files/{encoded_path}"

        # Base64 encode the content
        encoded_content = base64.b64encode(content.encode()).decode()

        data = {
            "branch": branch,
            "content": encoded_content,
            "commit_message": commit_message,
            "encoding": "base64"
        }

        method = "POST" if create else "PUT"
        return await self._make_request(endpoint, method=method, data=data)

    # Tag operations
    async def list_tags(self, project_id: str) -> List[Dict]:
        """List tags for a project"""
        endpoint = f"/api/v4/projects/{project_id}/repository/tags"
        return await self._make_request(endpoint)

    async def create_tag(self, project_id: str, tag_name: str, ref: str, message: str = None) -> Dict:
        """Create a new tag"""
        endpoint = f"/api/v4/projects/{project_id}/repository/tags"
        data = {"tag_name": tag_name, "ref": ref}
        if message:
            data["message"] = message
        return await self._make_request(endpoint, method="POST", data=data)

    # Commit operations
    async def list_commits(self, project_id: str, ref_name: str = None, since: str = None, until: str = None) -> List[Dict]:
        """List commits for a project"""
        endpoint = f"/api/v4/projects/{project_id}/repository/commits"
        params = []
        if ref_name:
            params.append(f"ref_name={ref_name}")
        if since:
            params.append(f"since={since}")
        if until:
            params.append(f"until={until}")
        if params:
            endpoint += f"?{'&'.join(params)}"
        return await self._make_request(endpoint)

    async def get_commit(self, project_id: str, sha: str) -> Dict:
        """Get a specific commit"""
        endpoint = f"/api/v4/projects/{project_id}/repository/commits/{sha}"
        return await self._make_request(endpoint)

    async def get_merge_request_changes(self, project_id: str, mr_iid: int) -> Dict:
        """Get the changes (diffs) for a specific merge request"""
        endpoint = f"/api/v4/projects/{project_id}/merge_requests/{mr_iid}/changes"
        return await self._make_request(endpoint)

    # Enhanced search and repository tree operations
    async def get_repository_tree(self, project_id: str, path: str = "", ref: str = "main",
                                 recursive: bool = False, per_page: int = 100) -> List[Dict]:
        """Get repository tree (files and directories)"""
        endpoint = f"/api/v4/projects/{project_id}/repository/tree"
        params = [f"ref={ref}", f"per_page={per_page}"]
        if path:
            params.append(f"path={quote(path, safe='')}")
        if recursive:
            params.append("recursive=true")

        endpoint += f"?{'&'.join(params)}"
        return await self._make_request(endpoint)

    async def search_files(self, project_id: str, pattern: str, ref: str = "main",
                          max_results: int = 100) -> List[Dict]:
        """Search for files matching a glob pattern"""
        import fnmatch

        # Get all files recursively
        tree = await self.get_repository_tree(project_id, "", ref, recursive=True, per_page=1000)

        # Filter files (not directories) that match the pattern
        matching_files = []
        for item in tree:
            if item.get("type") == "blob":  # blob = file
                file_path = item.get("path", "")
                if fnmatch.fnmatch(file_path, pattern):
                    matching_files.append(item)
                    if len(matching_files) >= max_results:
                        break

        return matching_files

    async def grep_repository_content(self, project_id: str, pattern: str,
                                    file_filter: str = None, ref: str = "main",
                                    case_insensitive: bool = False,
                                    context_lines: int = 0, max_files: int = 50) -> List[Dict]:
        """Search file contents for patterns (like grep -r)"""
        import re
        import fnmatch

        # Get all files, optionally filtered by pattern
        tree = await self.get_repository_tree(project_id, "", ref, recursive=True, per_page=1000)

        files_to_search = []
        for item in tree:
            if item.get("type") == "blob":  # blob = file
                file_path = item.get("path", "")

                # Apply file filter if provided
                if file_filter and not fnmatch.fnmatch(file_path, file_filter):
                    continue

                # Skip binary files
                if any(file_path.lower().endswith(ext) for ext in
                      ['.jpg', '.png', '.gif', '.pdf', '.zip', '.exe', '.bin', '.so']):
                    continue

                files_to_search.append(item)
                if len(files_to_search) >= max_files:
                    break

        # Compile regex pattern
        flags = re.IGNORECASE if case_insensitive else 0
        try:
            regex = re.compile(pattern, flags)
        except re.error:
            # If regex fails, treat as literal string
            regex = re.compile(re.escape(pattern), flags)

        matches = []
        for file_item in files_to_search:
            try:
                # Get file content
                file_content = await self.get_file(project_id, file_item["path"], ref)
                content = file_content.get("content", "")

                lines = content.split('\n')
                for line_num, line in enumerate(lines, 1):
                    if regex.search(line):
                        match_info = {
                            "file": file_item["path"],
                            "line_number": line_num,
                            "line": line.strip(),
                            "match": regex.search(line).group()
                        }

                        # Add context lines if requested
                        if context_lines > 0:
                            start = max(0, line_num - context_lines - 1)
                            end = min(len(lines), line_num + context_lines)
                            match_info["context"] = lines[start:end]

                        matches.append(match_info)

            except Exception as e:
                logger.warning(f"Failed to search in {file_item['path']}: {e}")
                continue

        return matches

    async def search_commits_enhanced(self, project_id: str, grep: str = None, author: str = None,
                                    file_path: str = None, since: str = None, until: str = None,
                                    limit: int = 20) -> List[Dict]:
        """Enhanced commit search with filtering like git log --grep"""
        import re

        # Get commits with basic filters
        commits = await self.list_commits(project_id, since=since, until=until)

        filtered_commits = []
        for commit in commits[:limit * 3]:  # Get more than needed for filtering
            # Apply grep filter on commit message
            if grep:
                try:
                    if not re.search(grep, commit.get("message", ""), re.IGNORECASE):
                        continue
                except re.error:
                    # Fallback to simple string search
                    if grep.lower() not in commit.get("message", "").lower():
                        continue

            # Apply author filter
            if author:
                author_name = commit.get("author_name", "")
                author_email = commit.get("author_email", "")
                if author.lower() not in author_name.lower() and author.lower() not in author_email.lower():
                    continue

            filtered_commits.append(commit)
            if len(filtered_commits) >= limit:
                break

        # If file_path is specified, we'd need to check commit diffs (more complex)
        # For now, return the filtered commits
        return filtered_commits



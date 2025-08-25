"""
api/vcs.py
──────────
VCS integration layer for Triangulum.
"""

import os
import requests
from typing import Any, Dict, List, Optional

# --- Base Provider ---

class VCSProvider:
    """Base class for VCS providers."""
    def __init__(self, api_key: str):
        self.api_key = api_key

    def create_pull_request(self, repo: str, title: str, body: str, head: str, base: str) -> Dict[str, Any]:
        raise NotImplementedError

    def post_comment(self, repo: str, pr_number: int, comment: str) -> Dict[str, Any]:
        raise NotImplementedError

    def update_commit_status(self, repo: str, commit_sha: str, state: str, description: str, context: str) -> Dict[str, Any]:
        raise NotImplementedError

# --- GitHub Implementation ---

class GitHubProvider(VCSProvider):
    """GitHub integration."""
    API_URL = "https://api.github.com"

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"token {self.api_key}",
            "Accept": "application/vnd.github.v3+json",
        }

    def create_pull_request(self, repo: str, title: str, body: str, head: str, base: str) -> Dict[str, Any]:
        url = f"{self.API_URL}/repos/{repo}/pulls"
        data = {"title": title, "body": body, "head": head, "base": base}
        response = requests.post(url, headers=self._get_headers(), json=data)
        response.raise_for_status()
        return response.json()

    def post_comment(self, repo: str, pr_number: int, comment: str) -> Dict[str, Any]:
        url = f"{self.API_URL}/repos/{repo}/issues/{pr_number}/comments"
        data = {"body": comment}
        response = requests.post(url, headers=self._get_headers(), json=data)
        response.raise_for_status()
        return response.json()

    def update_commit_status(self, repo: str, commit_sha: str, state: str, description: str, context: str) -> Dict[str, Any]:
        """State can be one of: error, failure, pending, success"""
        url = f"{self.API_URL}/repos/{repo}/statuses/{commit_sha}"
        data = {"state": state, "description": description, "context": context}
        response = requests.post(url, headers=self._get_headers(), json=data)
        response.raise_for_status()
        return response.json()

# --- Manager ---

class VCSManager:
    """VCS Manager for Triangulum."""
    def __init__(self):
        self.providers: Dict[str, VCSProvider] = {}
        self._autodetect_providers()

    def _autodetect_providers(self):
        """Autodetect available VCS providers based on environment variables."""
        # As defined in the system_config.yaml schema, we look for GITHUB_TOKEN.
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            self.providers["github"] = GitHubProvider(github_token)

    def get_provider(self, provider_name: str) -> Optional[VCSProvider]:
        return self.providers.get(provider_name)

    def get_default_provider(self) -> Optional[VCSProvider]:
        if "github" in self.providers:
            return self.providers["github"]
        return None

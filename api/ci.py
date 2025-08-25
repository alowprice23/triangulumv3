"""
api/ci.py
─────────
CI/CD integration layer for Triangulum.
"""

import os
import requests
import zipfile
import io
from typing import Any, Dict, List, Optional

# --- Base Provider ---

class CIProvider:
    """Base class for CI/CD providers."""
    def __init__(self, api_key: str):
        self.api_key = api_key

    def trigger_pipeline(self, repo: str, workflow_id: str, ref: str, inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        raise NotImplementedError

    def get_pipeline_status(self, repo: str, run_id: str) -> Dict[str, Any]:
        raise NotImplementedError

    def download_artifact(self, repo: str, run_id: str, artifact_name: str, download_path: str) -> bool:
        raise NotImplementedError

# --- GitHub Implementation ---

class GitHubActionsProvider(CIProvider):
    """GitHub Actions integration."""
    API_URL = "https://api.github.com"

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"token {self.api_key}",
            "Accept": "application/vnd.github.v3+json",
        }

    def trigger_pipeline(self, repo: str, workflow_id: str, ref: str, inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Triggers a GitHub Actions workflow using workflow_dispatch."""
        url = f"{self.API_URL}/repos/{repo}/actions/workflows/{workflow_id}/dispatches"
        data = {"ref": ref, "inputs": inputs or {}}
        response = requests.post(url, headers=self._get_headers(), json=data)
        response.raise_for_status()
        # The response for a dispatch is empty (204), so we return our own status.
        return {"status": "success", "message": f"Workflow {workflow_id} triggered successfully on ref {ref}."}

    def get_pipeline_status(self, repo: str, run_id: str) -> Dict[str, Any]:
        """Gets the status of a GitHub Actions workflow run."""
        url = f"{self.API_URL}/repos/{repo}/actions/runs/{run_id}"
        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json()

    def download_artifact(self, repo: str, run_id: str, artifact_name: str, download_path: str) -> bool:
        """Downloads an artifact from a GitHub Actions workflow run."""
        # First, list the artifacts for the run to get the artifact ID
        list_url = f"{self.API_URL}/repos/{repo}/actions/runs/{run_id}/artifacts"
        list_response = requests.get(list_url, headers=self._get_headers())
        list_response.raise_for_status()
        artifacts = list_response.json().get("artifacts", [])

        artifact_id = None
        for art in artifacts:
            if art["name"] == artifact_name:
                artifact_id = art["id"]
                break

        if not artifact_id:
            raise FileNotFoundError(f"Artifact '{artifact_name}' not found in run '{run_id}'.")

        # Then, download the artifact archive
        download_url = f"{self.API_URL}/repos/{repo}/actions/artifacts/{artifact_id}/zip"
        download_response = requests.get(download_url, headers=self._get_headers(), stream=True)
        download_response.raise_for_status()

        # Artifacts are downloaded as zip archives, we need to extract them.
        with zipfile.ZipFile(io.BytesIO(download_response.content)) as z:
            z.extractall(download_path)

        return True

# --- Manager ---

class CIManager:
    """CI/CD Manager for Triangulum."""
    def __init__(self):
        self.providers: Dict[str, CIProvider] = {}
        self._autodetect_providers()

    def _autodetect_providers(self):
        """Autodetect available CI/CD providers based on environment variables."""
        # As defined in the system_config.yaml schema, we look for GITHUB_TOKEN.
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            self.providers["github_actions"] = GitHubActionsProvider(github_token)

    def get_provider(self, provider_name: str) -> Optional[CIProvider]:
        return self.providers.get(provider_name)

    def get_default_provider(self) -> Optional[CIProvider]:
        if "github_actions" in self.providers:
            return self.providers["github_actions"]
        return None

"""Client for Agent Zero MCP integration."""

import httpx

from config import settings


class AgentZeroClient:
    """Client for Agent Zero MCP API."""

    def __init__(self):
        self.mcp_url = settings.agent_zero_mcp_url

    async def analyze_github_repo(self, repo_url: str, branch: str = "main") -> dict:
        """
        Analyze a GitHub repository for primitives-first conversion.

        Returns analysis report with:
        - benefits: list of benefits from conversion
        - current_architecture: analysis of current code
        - suggested_plan: Maicrosoft plan YAML
        - coverage_estimate: percentage of code covered by primitives
        - gaps: list of functionality gaps
        """
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                self.mcp_url,
                json={
                    "method": "analyze_repository",
                    "params": {
                        "repo_url": repo_url,
                        "branch": branch,
                        "analysis_type": "primitives_conversion",
                    }
                }
            )
            response.raise_for_status()
            return response.json()


agent_zero = AgentZeroClient()

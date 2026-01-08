"""Tests for the MCP server."""

import pytest
import json

from maicrosoft.mcp.server import MCPServer


@pytest.fixture
def mcp_server():
    """Get MCP server instance."""
    return MCPServer(primitives_path="primitives")


class TestMCPServer:
    """Tests for MCP server."""

    @pytest.mark.asyncio
    async def test_list_particles(self, mcp_server):
        """Test listing particles."""
        result = await mcp_server._list_particles({})

        assert len(result) == 1
        data = json.loads(result[0].text)

        assert "count" in data
        assert "particles" in data
        assert data["count"] > 0
        assert len(data["particles"]) > 0

    @pytest.mark.asyncio
    async def test_list_particles_with_filter(self, mcp_server):
        """Test listing particles with category filter."""
        result = await mcp_server._list_particles({"category": "io"})

        data = json.loads(result[0].text)
        assert "particles" in data
        # All returned particles should have category "io"
        for p in data["particles"]:
            assert p["category"] == "io"

    @pytest.mark.asyncio
    async def test_get_primitive(self, mcp_server):
        """Test getting a specific primitive."""
        result = await mcp_server._get_primitive({"primitive_id": "P001"})

        data = json.loads(result[0].text)
        assert data["id"] == "P001"
        assert "name" in data
        assert "description" in data
        assert "interface" in data

    @pytest.mark.asyncio
    async def test_get_primitive_not_found(self, mcp_server):
        """Test getting a non-existent primitive."""
        result = await mcp_server._get_primitive({"primitive_id": "P999"})

        data = json.loads(result[0].text)
        assert "error" in data
        assert "not found" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_get_primitive_missing_id(self, mcp_server):
        """Test getting primitive without ID."""
        result = await mcp_server._get_primitive({})

        data = json.loads(result[0].text)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_validate_plan_valid(self, mcp_server):
        """Test validating a valid plan."""
        plan = {
            "metadata": {
                "id": "test-plan",
                "name": "Test Plan",
                "version": "1.0.0",
            },
            "settings": {"allow_fallback": False},
            "trigger": {"type": "manual"},
            "nodes": [
                {
                    "id": "step1",
                    "primitive_id": "P001",
                    "inputs": {
                        "method": "GET",
                        "url": "https://example.com",
                    },
                }
            ],
            "edges": [],
        }

        result = await mcp_server._validate_plan({"plan": plan})
        data = json.loads(result[0].text)

        assert data["valid"] is True
        assert len(data["errors"]) == 0

    @pytest.mark.asyncio
    async def test_validate_plan_invalid_primitive(self, mcp_server):
        """Test validating a plan with invalid primitive."""
        plan = {
            "metadata": {
                "id": "test-plan",
                "name": "Test Plan",
                "version": "1.0.0",
            },
            "settings": {"allow_fallback": False},
            "trigger": {"type": "manual"},
            "nodes": [
                {
                    "id": "step1",
                    "primitive_id": "P999",  # Invalid
                    "inputs": {},
                }
            ],
            "edges": [],
        }

        result = await mcp_server._validate_plan({"plan": plan})
        data = json.loads(result[0].text)

        assert data["valid"] is False
        assert len(data["errors"]) > 0

    @pytest.mark.asyncio
    async def test_compile_plan(self, mcp_server):
        """Test compiling a valid plan."""
        plan = {
            "metadata": {
                "id": "test-plan",
                "name": "Test Plan",
                "version": "1.0.0",
            },
            "settings": {"allow_fallback": False},
            "trigger": {"type": "manual"},
            "nodes": [
                {
                    "id": "step1",
                    "primitive_id": "P010",
                    "inputs": {
                        "level": "info",
                        "message": "Hello",
                    },
                }
            ],
            "edges": [],
        }

        result = await mcp_server._compile_plan({"plan": plan, "target": "n8n"})
        data = json.loads(result[0].text)

        assert "nodes" in data
        assert "connections" in data
        assert "name" in data

    @pytest.mark.asyncio
    async def test_compile_plan_invalid(self, mcp_server):
        """Test compiling an invalid plan."""
        plan = {
            "metadata": {
                "id": "test-plan",
                "name": "Test Plan",
                "version": "1.0.0",
            },
            "settings": {"allow_fallback": False},
            "trigger": {"type": "manual"},
            "nodes": [
                {
                    "id": "step1",
                    "primitive_id": "P999",  # Invalid
                    "inputs": {},
                }
            ],
            "edges": [],
        }

        result = await mcp_server._compile_plan({"plan": plan})
        data = json.loads(result[0].text)

        assert "error" in data

    @pytest.mark.asyncio
    async def test_find_similar(self, mcp_server):
        """Test finding similar primitives."""
        result = await mcp_server._find_similar({"query": "http request api call"})

        data = json.loads(result[0].text)
        assert "results" in data
        assert "count" in data
        assert data["count"] > 0

        # P001 (http_call) should be in results
        ids = [r["id"] for r in data["results"]]
        assert "P001" in ids

    @pytest.mark.asyncio
    async def test_find_similar_with_limit(self, mcp_server):
        """Test finding similar primitives with limit."""
        result = await mcp_server._find_similar({"query": "data", "limit": 3})

        data = json.loads(result[0].text)
        assert len(data["results"]) <= 3

    @pytest.mark.asyncio
    async def test_find_similar_no_match(self, mcp_server):
        """Test finding similar with no matches."""
        result = await mcp_server._find_similar({"query": "xyznonexistent123"})

        data = json.loads(result[0].text)
        assert data["count"] == 0
        assert len(data["results"]) == 0

"""MCP server for Maicrosoft primitives-first AI coding framework.

Exposes tools for AI agents to interact with the primitives registry,
validate plans, and compile workflows.
"""

from typing import Any
from dataclasses import dataclass

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    Server = None  # type: ignore
    Tool = None  # type: ignore
    stdio_server = None  # type: ignore

    @dataclass
    class TextContent:
        """Fallback TextContent when MCP not installed."""
        type: str
        text: str

from maicrosoft.registry import PrimitiveRegistry
from maicrosoft.validation import PlanValidator
from maicrosoft.compiler import N8NCompiler
from maicrosoft.core.models import Plan


class MCPServer:
    """MCP server exposing Maicrosoft primitives tools."""

    def __init__(self, primitives_path: str = "primitives"):
        """Initialize MCP server with registry and validator.

        Args:
            primitives_path: Path to primitives directory
        """
        self.registry = PrimitiveRegistry(primitives_path)
        self.validator = PlanValidator(self.registry)
        self.compiler = N8NCompiler(self.registry)

        if MCP_AVAILABLE:
            self.server = Server("maicrosoft")
            self._register_tools()
        else:
            self.server = None

    def _register_tools(self) -> None:
        """Register all MCP tools."""
        if not self.server:
            return

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available MCP tools."""
            return [
                Tool(
                    name="list_particles",
                    description="List all available particles in the registry with their IDs, names, and descriptions",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": "Filter by category (e.g., 'data', 'control', 'io')",
                            },
                            "status": {
                                "type": "string",
                                "enum": ["stable", "beta", "deprecated"],
                                "description": "Filter by stability status",
                            },
                        },
                    },
                ),
                Tool(
                    name="get_primitive",
                    description="Get full definition of a primitive by ID, including interface schema and examples",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "primitive_id": {
                                "type": "string",
                                "description": "Primitive ID (e.g., 'P001', 'A001', 'M001')",
                            },
                        },
                        "required": ["primitive_id"],
                    },
                ),
                Tool(
                    name="validate_plan",
                    description="Validate a Plan JSON against all rules: syntax, registry, interface, dependencies, policies",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "plan": {
                                "type": "object",
                                "description": "Plan JSON/YAML to validate",
                            },
                        },
                        "required": ["plan"],
                    },
                ),
                Tool(
                    name="compile_plan",
                    description="Compile a validated Plan JSON to target format (N8N workflow)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "plan": {
                                "type": "object",
                                "description": "Plan JSON to compile",
                            },
                            "target": {
                                "type": "string",
                                "enum": ["n8n"],
                                "description": "Target compilation format",
                                "default": "n8n",
                            },
                        },
                        "required": ["plan"],
                    },
                ),
                Tool(
                    name="find_similar",
                    description="Search for primitives by semantic similarity to a query",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Natural language description of desired functionality",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results",
                                "default": 5,
                            },
                        },
                        "required": ["query"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Handle tool calls."""
            if name == "list_particles":
                return await self._list_particles(arguments)
            elif name == "get_primitive":
                return await self._get_primitive(arguments)
            elif name == "validate_plan":
                return await self._validate_plan(arguments)
            elif name == "compile_plan":
                return await self._compile_plan(arguments)
            elif name == "find_similar":
                return await self._find_similar(arguments)
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

    async def _list_particles(self, args: dict[str, Any]) -> list[TextContent]:
        """List all particles with optional filtering."""
        import json

        category = args.get("category")
        status = args.get("status", "stable")

        # Get list with filters applied
        primitives = self.registry.list(category=category, status=status)

        particles = []
        for p in primitives:
            particles.append({
                "id": p.get("id"),
                "name": p.get("name"),
                "description": p.get("description"),
                "category": p.get("category"),
                "status": p.get("status"),
                "tags": p.get("tags", []),
            })

        result = {
            "count": len(particles),
            "particles": particles,
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _get_primitive(self, args: dict[str, Any]) -> list[TextContent]:
        """Get full primitive definition."""
        import json

        primitive_id = args.get("primitive_id")
        if not primitive_id:
            return [TextContent(type="text", text='{"error": "primitive_id is required"}')]

        try:
            primitive = self.registry.get(primitive_id)
        except FileNotFoundError:
            return [TextContent(
                type="text",
                text=f'{{"error": "Primitive not found: {primitive_id}"}}'
            )]

        result = {
            "id": primitive.metadata.id,
            "name": primitive.metadata.name,
            "description": primitive.metadata.description,
            "category": primitive.metadata.category.value if primitive.metadata.category else None,
            "status": primitive.metadata.status.value,
            "tags": primitive.metadata.tags,
            "interface": {
                "inputs": [inp.model_dump() for inp in primitive.interface.inputs],
                "outputs": [out.model_dump() for out in primitive.interface.outputs],
            },
            "examples": [ex.model_dump() for ex in primitive.examples] if primitive.examples else [],
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _validate_plan(self, args: dict[str, Any]) -> list[TextContent]:
        """Validate a plan against all rules."""
        import json

        plan_data = args.get("plan")
        if not plan_data:
            return [TextContent(type="text", text='{"error": "plan is required"}')]

        try:
            # Parse plan
            plan = Plan.model_validate(plan_data)

            # Run validation
            result = self.validator.validate(plan)

            return [TextContent(type="text", text=json.dumps({
                "valid": result.valid,
                "errors": [{"level": v.level, "code": v.code, "message": v.message, "node_id": v.node_id}
                          for v in result.violations],
                "warnings": [{"level": w.level, "code": w.code, "message": w.message, "node_id": w.node_id}
                            for w in result.warnings],
            }, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=f'{{"error": "Validation failed: {str(e)}"}}')]

    async def _compile_plan(self, args: dict[str, Any]) -> list[TextContent]:
        """Compile plan to target format."""
        import json

        plan_data = args.get("plan")
        target = args.get("target", "n8n")

        if not plan_data:
            return [TextContent(type="text", text='{"error": "plan is required"}')]

        try:
            # Parse plan
            plan = Plan.model_validate(plan_data)

            # Validate first
            validation = self.validator.validate(plan)
            if not validation.valid:
                return [TextContent(type="text", text=json.dumps({
                    "error": "Plan validation failed",
                    "errors": [{"level": v.level, "code": v.code, "message": v.message} for v in validation.violations],
                }, indent=2))]

            # Compile
            if target == "n8n":
                workflow = self.compiler.compile(plan)
                return [TextContent(type="text", text=json.dumps(workflow, indent=2))]
            else:
                return [TextContent(type="text", text=f'{{"error": "Unsupported target: {target}"}}')]
        except Exception as e:
            return [TextContent(type="text", text=f'{{"error": "Compilation failed: {str(e)}"}}')]

    async def _find_similar(self, args: dict[str, Any]) -> list[TextContent]:
        """Find primitives by semantic similarity."""
        import json

        query = args.get("query", "")
        limit = args.get("limit", 5)

        if not query:
            return [TextContent(type="text", text='{"error": "query is required"}')]

        # Simple keyword-based search (can be enhanced with embeddings)
        query_lower = query.lower()
        query_words = set(query_lower.split())

        scored_primitives = []
        for p in self.registry.list(status=None):
            score = 0

            # Check name match
            name = p.get("name", "").lower()
            if query_lower in name:
                score += 10

            # Check description match
            desc_lower = p.get("description", "").lower()
            for word in query_words:
                if word in desc_lower:
                    score += 2

            # Check tag match
            tags = p.get("tags", [])
            for tag in tags:
                if tag.lower() in query_lower or query_lower in tag.lower():
                    score += 5

            if score > 0:
                scored_primitives.append({
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "description": p.get("description"),
                    "score": score,
                    "tags": tags,
                })

        # Sort by score and limit
        scored_primitives.sort(key=lambda x: x["score"], reverse=True)
        results = scored_primitives[:limit]

        return [TextContent(type="text", text=json.dumps({
            "query": query,
            "count": len(results),
            "results": results,
        }, indent=2))]

    async def run(self) -> None:
        """Run the MCP server."""
        if not MCP_AVAILABLE:
            raise RuntimeError(
                "MCP dependencies not available. Install with: pip install maicrosoft[mcp]"
            )

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, self.server.create_initialization_options())


def create_server(primitives_path: str = "primitives") -> MCPServer:
    """Create and configure MCP server instance.

    Args:
        primitives_path: Path to primitives directory

    Returns:
        Configured MCPServer instance
    """
    return MCPServer(primitives_path)


async def main() -> None:
    """Main entry point for MCP server."""
    import sys

    # Get primitives path from args or use default
    primitives_path = sys.argv[1] if len(sys.argv) > 1 else "primitives"

    server = create_server(primitives_path)
    await server.run()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

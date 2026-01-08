"""Tests for the N8N compiler."""

import pytest
import json

from maicrosoft.core.models import (
    Plan,
    PlanMetadata,
    PlanSettings,
    Trigger,
    PlanNode,
    Edge,
)
from maicrosoft.compiler import N8NCompiler
from maicrosoft.registry import PrimitiveRegistry


@pytest.fixture
def registry():
    """Get primitive registry."""
    return PrimitiveRegistry()


@pytest.fixture
def compiler(registry):
    """Get N8N compiler."""
    return N8NCompiler(registry)


@pytest.fixture
def simple_plan():
    """Create a simple test plan."""
    return Plan(
        metadata=PlanMetadata(
            id="test-plan-001",
            name="Test Plan",
            version="1.0.0",
        ),
        settings=PlanSettings(
            allow_fallback=False,
            risk_level="low",
        ),
        trigger=Trigger(
            type="manual",
            config={},
        ),
        nodes=[
            PlanNode(
                id="fetch_data",
                primitive_id="P001",
                inputs={
                    "method": "GET",
                    "url": "https://api.example.com/data",
                },
            ),
            PlanNode(
                id="log_result",
                primitive_id="P010",
                inputs={
                    "level": "info",
                    "message": "Data fetched successfully",
                },
            ),
        ],
        edges=[
            Edge(
                from_node="fetch_data",
                to_node="log_result",
            ),
        ],
    )


class TestN8NCompiler:
    """Tests for N8N compiler."""

    def test_compile_simple_plan(self, compiler, simple_plan):
        """Test compiling a simple plan."""
        result = compiler.compile(simple_plan)

        assert "name" in result
        assert result["name"] == "Test Plan"
        assert "nodes" in result
        assert "connections" in result
        assert len(result["nodes"]) == 3  # 2 nodes + trigger

    def test_compile_creates_trigger_node(self, compiler, simple_plan):
        """Test that compiler creates a trigger node."""
        result = compiler.compile(simple_plan)

        trigger_nodes = [n for n in result["nodes"] if "manualTrigger" in n["type"]]
        assert len(trigger_nodes) == 1

    def test_compile_http_request_node(self, compiler, simple_plan):
        """Test HTTP request node compilation."""
        result = compiler.compile(simple_plan)

        http_nodes = [n for n in result["nodes"] if "httpRequest" in n["type"]]
        assert len(http_nodes) == 1

        http_node = http_nodes[0]
        assert http_node["parameters"]["method"] == "GET"
        assert "api.example.com" in http_node["parameters"]["url"]

    def test_compile_creates_connections(self, compiler, simple_plan):
        """Test that compiler creates proper connections."""
        result = compiler.compile(simple_plan)

        assert "connections" in result
        # Should have connections from trigger to first node, and first to second
        connection_count = sum(
            len(conns)
            for node_conns in result["connections"].values()
            for conns in node_conns.values()
        )
        assert connection_count >= 2

    def test_compile_with_webhook_trigger(self, compiler, registry):
        """Test compilation with webhook trigger."""
        plan = Plan(
            metadata=PlanMetadata(
                id="webhook-plan",
                name="Webhook Plan",
                version="1.0.0",
            ),
            settings=PlanSettings(),
            trigger=Trigger(
                type="webhook",
                config={"path": "/my-webhook"},
            ),
            nodes=[
                PlanNode(
                    id="log_it",
                    primitive_id="P010",
                    inputs={"level": "info", "message": "Webhook received"},
                ),
            ],
            edges=[],
        )

        result = compiler.compile(plan)
        webhook_nodes = [n for n in result["nodes"] if "webhook" in n["type"]]
        assert len(webhook_nodes) == 1

    def test_compile_with_schedule_trigger(self, compiler, registry):
        """Test compilation with schedule trigger."""
        plan = Plan(
            metadata=PlanMetadata(
                id="schedule-plan",
                name="Schedule Plan",
                version="1.0.0",
            ),
            settings=PlanSettings(),
            trigger=Trigger(
                type="schedule",
                config={"cron": "0 9 * * *"},
            ),
            nodes=[
                PlanNode(
                    id="log_it",
                    primitive_id="P010",
                    inputs={"level": "info", "message": "Scheduled run"},
                ),
            ],
            edges=[],
        )

        result = compiler.compile(plan)
        schedule_nodes = [n for n in result["nodes"] if "scheduleTrigger" in n["type"]]
        assert len(schedule_nodes) == 1

    def test_compile_transform_node(self, compiler, registry):
        """Test transform particle compilation."""
        plan = Plan(
            metadata=PlanMetadata(id="transform-plan", name="Transform", version="1.0.0"),
            settings=PlanSettings(),
            trigger=Trigger(type="manual"),
            nodes=[
                PlanNode(
                    id="transform",
                    primitive_id="P004",
                    inputs={
                        "operation": "map",
                        "source": "{{ ref: input.data }}",
                        "template": '{"name": "{{ item.name }}"}',
                    },
                ),
            ],
            edges=[],
        )

        result = compiler.compile(plan)
        code_nodes = [n for n in result["nodes"] if "code" in n["type"].lower()]
        assert len(code_nodes) == 1

    def test_compile_branch_node(self, compiler, registry):
        """Test branch particle compilation."""
        plan = Plan(
            metadata=PlanMetadata(id="branch-plan", name="Branch", version="1.0.0"),
            settings=PlanSettings(),
            trigger=Trigger(type="manual"),
            nodes=[
                PlanNode(
                    id="check",
                    primitive_id="P005",
                    inputs={
                        "condition": "{{ ref: input.value }} > 10",
                    },
                ),
            ],
            edges=[],
        )

        result = compiler.compile(plan)
        if_nodes = [n for n in result["nodes"] if "if" in n["type"].lower()]
        assert len(if_nodes) == 1

    def test_compile_loop_node(self, compiler, registry):
        """Test loop particle compilation."""
        plan = Plan(
            metadata=PlanMetadata(id="loop-plan", name="Loop", version="1.0.0"),
            settings=PlanSettings(),
            trigger=Trigger(type="manual"),
            nodes=[
                PlanNode(
                    id="iterate",
                    primitive_id="P006",
                    inputs={
                        "source": "{{ ref: input.items }}",
                    },
                ),
            ],
            edges=[],
        )

        result = compiler.compile(plan)
        loop_nodes = [n for n in result["nodes"] if "splitInBatches" in n["type"]]
        assert len(loop_nodes) == 1

    def test_compile_output_is_valid_json(self, compiler, simple_plan):
        """Test that output is valid JSON."""
        result = compiler.compile(simple_plan)

        # Should be serializable to JSON
        json_str = json.dumps(result)
        assert json_str
        assert isinstance(json.loads(json_str), dict)

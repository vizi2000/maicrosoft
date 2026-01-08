"""Tests for plan validation."""

import pytest
from pathlib import Path

from maicrosoft.core.models import (
    Plan,
    PlanMetadata,
    PlanNode,
    PlanSettings,
    Edge,
    CodeBlock,
)
from maicrosoft.registry.registry import PrimitiveRegistry
from maicrosoft.validation.validator import PlanValidator


class TestPlanValidator:
    """Tests for PlanValidator."""

    @pytest.fixture
    def registry(self) -> PrimitiveRegistry:
        """Create a registry."""
        primitives_dir = Path(__file__).parent.parent / "primitives"
        return PrimitiveRegistry(primitives_dir)

    @pytest.fixture
    def validator(self, registry: PrimitiveRegistry) -> PlanValidator:
        """Create a validator."""
        return PlanValidator(registry)

    def test_valid_plan(self, validator: PlanValidator) -> None:
        """Test validation of a valid plan."""
        plan = Plan(
            metadata=PlanMetadata(id="test-plan", name="Test Plan"),
            nodes=[
                PlanNode(
                    id="step1",
                    primitive_id="P001",
                    inputs={"method": "GET", "url": "https://example.com"},
                )
            ],
        )

        result = validator.validate(plan)
        assert result.valid is True
        assert len(result.violations) == 0

    def test_missing_primitive(self, validator: PlanValidator) -> None:
        """Test validation fails for non-existent primitive."""
        plan = Plan(
            metadata=PlanMetadata(id="test-plan", name="Test Plan"),
            nodes=[
                PlanNode(
                    id="step1",
                    primitive_id="P999",
                    inputs={},
                )
            ],
        )

        result = validator.validate(plan)
        assert result.valid is False
        assert any(v.code == "PRIMITIVE_NOT_FOUND" for v in result.violations)

    def test_missing_required_input(self, validator: PlanValidator) -> None:
        """Test validation fails for missing required input."""
        plan = Plan(
            metadata=PlanMetadata(id="test-plan", name="Test Plan"),
            nodes=[
                PlanNode(
                    id="step1",
                    primitive_id="P001",
                    inputs={"method": "GET"},
                )
            ],
        )

        result = validator.validate(plan)
        assert result.valid is False
        assert any(v.code == "INTERFACE_VIOLATION" for v in result.violations)

    def test_fallback_not_allowed(self, validator: PlanValidator) -> None:
        """Test that fallback requires allow_fallback=true."""
        plan = Plan(
            metadata=PlanMetadata(id="test-plan", name="Test Plan"),
            settings=PlanSettings(allow_fallback=False),
            nodes=[
                PlanNode(
                    id="step1",
                    primitive_id=None,
                    fallback=CodeBlock(
                        language="javascript",
                        code="return 1",
                        description="Test",
                    ),
                )
            ],
        )

        result = validator.validate(plan)
        assert result.valid is False
        assert any(v.code == "FALLBACK_NOT_ALLOWED" for v in result.violations)

    def test_fallback_allowed(self, validator: PlanValidator) -> None:
        """Test that fallback works when allowed."""
        plan = Plan(
            metadata=PlanMetadata(id="test-plan", name="Test Plan"),
            settings=PlanSettings(allow_fallback=True),
            nodes=[
                PlanNode(
                    id="step1",
                    primitive_id=None,
                    fallback=CodeBlock(
                        language="javascript",
                        code="return 1",
                        description="Test",
                    ),
                )
            ],
        )

        result = validator.validate(plan)
        assert result.valid is True

    def test_circular_dependency(self, validator: PlanValidator) -> None:
        """Test detection of circular dependencies."""
        plan = Plan(
            metadata=PlanMetadata(id="test-plan", name="Test Plan"),
            nodes=[
                PlanNode(id="a", primitive_id="P001", inputs={"method": "GET", "url": "http://a"}),
                PlanNode(id="b", primitive_id="P001", inputs={"method": "GET", "url": "http://b"}),
                PlanNode(id="c", primitive_id="P001", inputs={"method": "GET", "url": "http://c"}),
            ],
            edges=[
                Edge(from_node="a", to_node="b"),
                Edge(from_node="b", to_node="c"),
                Edge(from_node="c", to_node="a"),
            ],
        )

        result = validator.validate(plan)
        assert result.valid is False
        assert any(v.code == "CIRCULAR_DEPENDENCY" for v in result.violations)

    def test_duplicate_node_id(self, validator: PlanValidator) -> None:
        """Test detection of duplicate node IDs."""
        plan = Plan(
            metadata=PlanMetadata(id="test-plan", name="Test Plan"),
            nodes=[
                PlanNode(id="step1", primitive_id="P001", inputs={"method": "GET", "url": "http://a"}),
                PlanNode(id="step1", primitive_id="P001", inputs={"method": "GET", "url": "http://b"}),
            ],
        )

        result = validator.validate(plan)
        assert result.valid is False
        assert any(v.code == "DUPLICATE_NODE_ID" for v in result.violations)

    def test_empty_plan(self, validator: PlanValidator) -> None:
        """Test validation fails for empty plan."""
        plan = Plan(
            metadata=PlanMetadata(id="test-plan", name="Test Plan"),
            nodes=[],
        )

        result = validator.validate(plan)
        assert result.valid is False
        assert any(v.code == "EMPTY_PLAN" for v in result.violations)

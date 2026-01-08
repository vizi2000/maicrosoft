"""Plan validation pipeline."""

from __future__ import annotations

from typing import Any

from maicrosoft.core.models import (
    Plan,
    PlanNode,
    ValidationResult,
    ValidationViolation,
)
from maicrosoft.registry.registry import PrimitiveRegistry


class PlanValidator:
    """Validates plans through a multi-layer pipeline.

    Validation layers:
    1. SYNTAX - JSON Schema, primitive ID format
    2. REGISTRY - Primitive exists, not deprecated
    3. INTERFACE - Required inputs, type matching
    4. DEPENDENCY - No circular deps, hierarchy rules
    5. POLICY - Business rules (GDPR, SOC2, etc.)
    6. COMPILATION - Target-specific compatibility
    """

    def __init__(self, registry: PrimitiveRegistry | None = None):
        """Initialize validator.

        Args:
            registry: Primitive registry (creates default if None)
        """
        self.registry = registry or PrimitiveRegistry()

    def validate(self, plan: Plan) -> ValidationResult:
        """Run full validation pipeline.

        Args:
            plan: The plan to validate

        Returns:
            ValidationResult with valid flag and violations
        """
        violations: list[ValidationViolation] = []
        warnings: list[ValidationViolation] = []

        violations.extend(self._validate_syntax(plan))
        violations.extend(self._validate_registry(plan))
        violations.extend(self._validate_interface(plan))
        violations.extend(self._validate_dependencies(plan))
        warnings.extend(self._validate_policy(plan))

        return ValidationResult(
            valid=len(violations) == 0,
            violations=violations,
            warnings=warnings,
        )

    def _validate_syntax(self, plan: Plan) -> list[ValidationViolation]:
        """Layer 1: Syntax validation."""
        violations = []

        if not plan.metadata.id:
            violations.append(
                ValidationViolation(
                    level="error",
                    code="MISSING_PLAN_ID",
                    message="Plan must have an ID",
                )
            )

        if not plan.metadata.name:
            violations.append(
                ValidationViolation(
                    level="error",
                    code="MISSING_PLAN_NAME",
                    message="Plan must have a name",
                )
            )

        if not plan.nodes:
            violations.append(
                ValidationViolation(
                    level="error",
                    code="EMPTY_PLAN",
                    message="Plan must have at least one node",
                )
            )

        node_ids = set()
        for node in plan.nodes:
            if node.id in node_ids:
                violations.append(
                    ValidationViolation(
                        level="error",
                        code="DUPLICATE_NODE_ID",
                        message=f"Duplicate node ID: {node.id}",
                        node_id=node.id,
                    )
                )
            node_ids.add(node.id)

        return violations

    def _validate_registry(self, plan: Plan) -> list[ValidationViolation]:
        """Layer 2: Registry validation."""
        violations = []

        for node in plan.nodes:
            if node.primitive_id is None:
                if node.fallback is None:
                    violations.append(
                        ValidationViolation(
                            level="error",
                            code="NO_PRIMITIVE_OR_FALLBACK",
                            message="Node must have primitive_id or fallback",
                            node_id=node.id,
                        )
                    )
                elif not plan.settings.allow_fallback:
                    violations.append(
                        ValidationViolation(
                            level="error",
                            code="FALLBACK_NOT_ALLOWED",
                            message="Code fallback used but allow_fallback is false",
                            node_id=node.id,
                        )
                    )
                continue

            if not self.registry.exists(node.primitive_id):
                violations.append(
                    ValidationViolation(
                        level="error",
                        code="PRIMITIVE_NOT_FOUND",
                        message=f"Primitive not found: {node.primitive_id}",
                        node_id=node.id,
                    )
                )
                continue

            primitive = self.registry.get(node.primitive_id)
            if primitive.metadata.status.value == "deprecated":
                violations.append(
                    ValidationViolation(
                        level="error",
                        code="PRIMITIVE_DEPRECATED",
                        message=f"Primitive is deprecated: {node.primitive_id}",
                        node_id=node.id,
                    )
                )

            if primitive.metadata.status.value == "draft":
                violations.append(
                    ValidationViolation(
                        level="error",
                        code="PRIMITIVE_DRAFT",
                        message=f"Cannot use draft primitive in production: {node.primitive_id}",
                        node_id=node.id,
                    )
                )

        return violations

    def _validate_interface(self, plan: Plan) -> list[ValidationViolation]:
        """Layer 3: Interface validation."""
        violations = []

        for node in plan.nodes:
            if node.primitive_id is None:
                continue

            if not self.registry.exists(node.primitive_id):
                continue

            is_valid, errors = self.registry.validate_inputs(
                node.primitive_id, node.inputs
            )

            for error in errors:
                violations.append(
                    ValidationViolation(
                        level="error",
                        code="INTERFACE_VIOLATION",
                        message=error,
                        node_id=node.id,
                    )
                )

        return violations

    def _validate_dependencies(self, plan: Plan) -> list[ValidationViolation]:
        """Layer 4: Dependency validation."""
        violations = []

        node_ids = {node.id for node in plan.nodes}

        for edge in plan.edges:
            if edge.from_node not in node_ids:
                violations.append(
                    ValidationViolation(
                        level="error",
                        code="INVALID_EDGE_SOURCE",
                        message=f"Edge references non-existent node: {edge.from_node}",
                    )
                )
            if edge.to_node not in node_ids:
                violations.append(
                    ValidationViolation(
                        level="error",
                        code="INVALID_EDGE_TARGET",
                        message=f"Edge references non-existent node: {edge.to_node}",
                    )
                )

        if self._has_cycle(plan):
            violations.append(
                ValidationViolation(
                    level="error",
                    code="CIRCULAR_DEPENDENCY",
                    message="Plan contains circular dependencies",
                )
            )

        return violations

    def _has_cycle(self, plan: Plan) -> bool:
        """Check if plan has circular dependencies."""
        graph: dict[str, list[str]] = {node.id: [] for node in plan.nodes}
        for edge in plan.edges:
            if edge.from_node in graph:
                graph[edge.from_node].append(edge.to_node)

        visited: set[str] = set()
        rec_stack: set[str] = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node_id in graph:
            if node_id not in visited:
                if dfs(node_id):
                    return True

        return False

    def _validate_policy(self, plan: Plan) -> list[ValidationViolation]:
        """Layer 5: Policy validation (returns warnings)."""
        warnings = []

        fallback_count = sum(1 for node in plan.nodes if node.fallback is not None)
        if fallback_count > 0:
            warnings.append(
                ValidationViolation(
                    level="warning",
                    code="FALLBACK_USED",
                    message=f"Plan uses {fallback_count} code fallback(s) - requires review",
                )
            )

        for node in plan.nodes:
            if node.fallback and node.fallback.code:
                if "eval(" in node.fallback.code or "exec(" in node.fallback.code:
                    warnings.append(
                        ValidationViolation(
                            level="warning",
                            code="UNSAFE_CODE",
                            message="Fallback code contains potentially unsafe constructs",
                            node_id=node.id,
                        )
                    )

        if plan.settings.risk_level == "high":
            warnings.append(
                ValidationViolation(
                    level="warning",
                    code="HIGH_RISK_PLAN",
                    message="Plan is marked as high-risk - ensure proper approval",
                )
            )

        return warnings

    def validate_node(self, node: PlanNode) -> list[ValidationViolation]:
        """Validate a single node."""
        violations = []

        if node.primitive_id is None and node.fallback is None:
            violations.append(
                ValidationViolation(
                    level="error",
                    code="NO_PRIMITIVE_OR_FALLBACK",
                    message="Node must have primitive_id or fallback",
                    node_id=node.id,
                )
            )
            return violations

        if node.primitive_id:
            if not self.registry.exists(node.primitive_id):
                violations.append(
                    ValidationViolation(
                        level="error",
                        code="PRIMITIVE_NOT_FOUND",
                        message=f"Primitive not found: {node.primitive_id}",
                        node_id=node.id,
                    )
                )
            else:
                is_valid, errors = self.registry.validate_inputs(
                    node.primitive_id, node.inputs
                )
                for error in errors:
                    violations.append(
                        ValidationViolation(
                            level="error",
                            code="INTERFACE_VIOLATION",
                            message=error,
                            node_id=node.id,
                        )
                    )

        return violations

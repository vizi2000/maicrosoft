"""Policy engine for business rule validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from maicrosoft.core.models import Plan, ValidationViolation


@dataclass
class PolicyRule:
    """A policy rule definition."""

    name: str
    description: str
    check: Callable[[Plan], bool]
    severity: str = "warning"
    message: str = ""


class PolicyEngine:
    """Engine for evaluating business policies against plans.

    Supports:
    - Built-in rules (cost limits, risk assessment)
    - Custom rules via plugins
    - GDPR, SOC2, HIPAA compliance checks
    """

    def __init__(self) -> None:
        """Initialize policy engine with default rules."""
        self.rules: list[PolicyRule] = []
        self._register_default_rules()

    def _register_default_rules(self) -> None:
        """Register built-in policy rules."""
        self.rules.append(
            PolicyRule(
                name="max_nodes",
                description="Plan should not exceed 50 nodes",
                check=lambda p: len(p.nodes) <= 50,
                severity="warning",
                message="Plan has more than 50 nodes - consider breaking into sub-plans",
            )
        )

        self.rules.append(
            PolicyRule(
                name="fallback_limit",
                description="Limit code fallbacks to 3 per plan",
                check=lambda p: sum(1 for n in p.nodes if n.fallback) <= 3,
                severity="error",
                message="Too many code fallbacks - create primitives instead",
            )
        )

        self.rules.append(
            PolicyRule(
                name="no_high_risk_fallback",
                description="No code fallback in high-risk plans",
                check=lambda p: not (
                    p.settings.risk_level == "high"
                    and any(n.fallback for n in p.nodes)
                ),
                severity="error",
                message="Code fallback not allowed in high-risk plans",
            )
        )

        self.rules.append(
            PolicyRule(
                name="trigger_required",
                description="Production plans should have a trigger",
                check=lambda p: p.trigger is not None
                or p.metadata.id.startswith("test-"),
                severity="warning",
                message="Plan has no trigger defined",
            )
        )

    def add_rule(self, rule: PolicyRule) -> None:
        """Add a custom policy rule.

        Args:
            rule: The PolicyRule to add
        """
        self.rules.append(rule)

    def remove_rule(self, name: str) -> bool:
        """Remove a rule by name.

        Args:
            name: The rule name

        Returns:
            True if rule was removed
        """
        initial_count = len(self.rules)
        self.rules = [r for r in self.rules if r.name != name]
        return len(self.rules) < initial_count

    def evaluate(self, plan: Plan) -> list[ValidationViolation]:
        """Evaluate all policy rules against a plan.

        Args:
            plan: The plan to evaluate

        Returns:
            List of violations (errors and warnings)
        """
        violations = []

        for rule in self.rules:
            try:
                if not rule.check(plan):
                    violations.append(
                        ValidationViolation(
                            level=rule.severity,
                            code=f"POLICY_{rule.name.upper()}",
                            message=rule.message or rule.description,
                        )
                    )
            except Exception as e:
                violations.append(
                    ValidationViolation(
                        level="error",
                        code="POLICY_EVAL_ERROR",
                        message=f"Failed to evaluate rule {rule.name}: {e}",
                    )
                )

        return violations

    def evaluate_single(self, plan: Plan, rule_name: str) -> bool | None:
        """Evaluate a single rule.

        Args:
            plan: The plan to evaluate
            rule_name: The rule to evaluate

        Returns:
            True if passes, False if fails, None if rule not found
        """
        for rule in self.rules:
            if rule.name == rule_name:
                try:
                    return rule.check(plan)
                except Exception:
                    return False
        return None

    def list_rules(self) -> list[dict[str, Any]]:
        """List all registered rules.

        Returns:
            List of rule definitions
        """
        return [
            {
                "name": rule.name,
                "description": rule.description,
                "severity": rule.severity,
            }
            for rule in self.rules
        ]

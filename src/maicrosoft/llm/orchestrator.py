"""LLM Orchestrator for AI-assisted plan composition.

Uses LiteLLM for multi-provider LLM access with primitives-first approach.
AI generates Plan JSON referencing primitives by ID, never executable code.
"""

from __future__ import annotations

import json
from typing import Any

import litellm
from pydantic import BaseModel

from maicrosoft.core.models import Plan
from maicrosoft.registry import PrimitiveRegistry
from maicrosoft.validation import PlanValidator


class CompositionResult(BaseModel):
    """Result of plan composition."""

    success: bool
    plan: Plan | None = None
    plan_yaml: str | None = None
    raw_response: str = ""
    gaps: list[str] = []
    validation_errors: list[str] = []
    suggestions: list[str] = []


class LLMOrchestrator:
    """Orchestrates LLM calls for primitives-first plan composition."""

    SYSTEM_PROMPT = '''You are a Maicrosoft Plan Composer. Your job is to create workflow plans using ONLY the available primitives.

## ABSOLUTE RULES:
1. NEVER write executable code (Python, JavaScript, SQL, etc.)
2. ONLY reference primitives by their ID (P001, P002, etc.)
3. ALL primitive IDs must exist in the provided registry
4. Follow the exact Plan JSON schema

## Available Primitives:
{primitives_list}

## Plan JSON Format:
```yaml
metadata:
  id: "plan-<unique-id>"
  name: "Human-readable name"
  version: "1.0.0"

settings:
  allow_fallback: false
  risk_level: "low"  # low, medium, high

trigger:
  type: "manual"  # webhook, schedule, manual, event
  config: {{}}

nodes:
  - id: "step_1"
    primitive_id: "P001"  # Must be from available primitives
    inputs:
      # Inputs matching the primitive's interface

edges:
  - from_node: "step_1"
    to_node: "step_2"
```

## Reference Syntax:
- Reference another node's output: "{{{{ ref: node_id.output_field }}}}"
- Reference input parameters: "{{{{ input.param_name }}}}"
- Reference config values: "{{{{ config.key }}}}"

## Your Response:
1. Analyze the user's request
2. Identify which primitives are needed
3. Design the data flow between nodes
4. Output ONLY valid Plan YAML (no explanations outside the YAML)

If a required capability does NOT exist in the primitives list:
- Add a comment noting the gap: # GAP: need primitive for X
- Suggest using allow_fallback: true with a code block (max 500 chars)
'''

    def __init__(
        self,
        registry: PrimitiveRegistry | None = None,
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.2,
    ):
        """Initialize the LLM Orchestrator.

        Args:
            registry: Primitive registry instance
            model: LLM model to use (via LiteLLM)
            temperature: Sampling temperature
        """
        self.registry = registry or PrimitiveRegistry()
        self.validator = PlanValidator(self.registry)
        self.model = model
        self.temperature = temperature

    def _build_primitives_list(self) -> str:
        """Build formatted list of available primitives for the prompt."""
        lines = []
        for p in self.registry.list(status=None):
            # Get full primitive to access interface
            try:
                primitive = self.registry.get(p["id"])
                inputs = []
                for inp in primitive.interface.inputs:
                    req = "*" if inp.required else ""
                    inputs.append(f"{inp.name}{req}: {inp.type.value}")
                inputs_str = ", ".join(inputs) if inputs else "none"
            except Exception:
                inputs_str = "unknown"

            lines.append(
                f"- {p.get('id')}: {p.get('name')}\n"
                f"  Description: {p.get('description')}\n"
                f"  Inputs: {inputs_str}"
            )

        return "\n".join(lines) if lines else "No primitives available"

    def _extract_yaml_from_response(self, response: str) -> str:
        """Extract YAML content from LLM response."""
        # Look for YAML code block
        if "```yaml" in response:
            start = response.find("```yaml") + 7
            end = response.find("```", start)
            if end > start:
                return response[start:end].strip()

        # Look for generic code block
        if "```" in response:
            start = response.find("```") + 3
            # Skip language identifier if present
            if response[start:start + 10].strip().startswith(("yaml", "yml")):
                start = response.find("\n", start) + 1
            end = response.find("```", start)
            if end > start:
                return response[start:end].strip()

        # Return as-is if no code block
        return response.strip()

    def _detect_gaps(self, response: str) -> list[str]:
        """Detect gap comments in the response."""
        gaps = []
        for line in response.split("\n"):
            if "# GAP:" in line:
                gap = line.split("# GAP:")[1].strip()
                gaps.append(gap)
        return gaps

    def _parse_and_validate(self, yaml_content: str) -> tuple[Plan | None, list[str]]:
        """Parse YAML and validate the plan."""
        import yaml as yaml_lib

        errors = []

        try:
            plan_data = yaml_lib.safe_load(yaml_content)
        except Exception as e:
            return None, [f"YAML parse error: {str(e)}"]

        try:
            plan = Plan.model_validate(plan_data)
        except Exception as e:
            return None, [f"Plan model error: {str(e)}"]

        # Run validation
        result = self.validator.validate(plan)
        if not result.valid:
            for v in result.violations:
                errors.append(f"[{v.level}:{v.code}] {v.message}")

        return plan if result.valid else None, errors

    async def compose(
        self,
        description: str,
        context: dict[str, Any] | None = None,
        max_retries: int = 2,
    ) -> CompositionResult:
        """Compose a plan from natural language description.

        Args:
            description: Natural language description of the workflow
            context: Additional context (config values, examples, etc.)
            max_retries: Maximum validation retry attempts

        Returns:
            CompositionResult with plan or errors
        """
        primitives_list = self._build_primitives_list()
        system_prompt = self.SYSTEM_PROMPT.format(primitives_list=primitives_list)

        user_message = f"Create a plan for: {description}"
        if context:
            user_message += f"\n\nContext:\n```json\n{json.dumps(context, indent=2)}\n```"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        all_errors: list[str] = []
        raw_response = ""

        for attempt in range(max_retries + 1):
            try:
                response = await litellm.acompletion(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=4000,
                )

                raw_response = response.choices[0].message.content or ""
            except Exception as e:
                return CompositionResult(
                    success=False,
                    raw_response="",
                    validation_errors=[f"LLM call failed: {str(e)}"],
                )

            # Extract and parse YAML
            yaml_content = self._extract_yaml_from_response(raw_response)
            gaps = self._detect_gaps(raw_response)

            plan, errors = self._parse_and_validate(yaml_content)

            if plan:
                return CompositionResult(
                    success=True,
                    plan=plan,
                    plan_yaml=yaml_content,
                    raw_response=raw_response,
                    gaps=gaps,
                )

            all_errors.extend(errors)

            # Add error feedback for retry
            if attempt < max_retries:
                messages.append({"role": "assistant", "content": raw_response})
                messages.append({
                    "role": "user",
                    "content": f"The plan has validation errors:\n{chr(10).join(errors)}\n\nPlease fix and regenerate.",
                })

        return CompositionResult(
            success=False,
            raw_response=raw_response,
            gaps=self._detect_gaps(raw_response),
            validation_errors=all_errors,
            suggestions=[
                "Check that all primitive IDs exist in the registry",
                "Verify input types match primitive interfaces",
                "Ensure all required inputs are provided",
            ],
        )

    def compose_sync(
        self,
        description: str,
        context: dict[str, Any] | None = None,
        max_retries: int = 2,
    ) -> CompositionResult:
        """Synchronous version of compose."""
        import asyncio

        return asyncio.run(self.compose(description, context, max_retries))

    def search_primitives(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Search for relevant primitives by semantic similarity.

        Uses keyword matching (can be enhanced with embeddings).
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())

        scored = []
        for p in self.registry.list(status=None):
            score = 0

            # Name matching
            name_lower = p.get("name", "").lower()
            if query_lower in name_lower:
                score += 10
            for word in query_words:
                if word in name_lower:
                    score += 3

            # Description matching
            desc_lower = p.get("description", "").lower()
            for word in query_words:
                if word in desc_lower:
                    score += 2

            # Tag matching
            tags = p.get("tags", [])
            for tag in tags:
                if tag.lower() in query_lower:
                    score += 5

            if score > 0:
                scored.append({
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "description": p.get("description"),
                    "score": score,
                })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]

    def suggest_primitives(self, description: str) -> list[dict[str, Any]]:
        """Suggest primitives that might be useful for a given task description."""
        return self.search_primitives(description, limit=10)

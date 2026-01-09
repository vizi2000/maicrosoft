"""Bridge to Maicrosoft core library."""

import sys
from pathlib import Path

# Add maicrosoft to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "src"))

from maicrosoft.registry import PrimitiveRegistry
from maicrosoft.validation import PlanValidator
from maicrosoft.compiler import N8NCompiler
from maicrosoft.llm import LLMOrchestrator


class MaicrosoftBridge:
    """Bridge to Maicrosoft core functionality."""

    def __init__(self, primitives_path: str = "primitives"):
        self.registry = PrimitiveRegistry(primitives_path)
        self.validator = PlanValidator(self.registry)
        self.compiler = N8NCompiler(self.registry)
        self.orchestrator = LLMOrchestrator(self.registry)

    def list_primitives(self, category: str = None, status: str = "stable"):
        """List available primitives."""
        return self.registry.list(category=category, status=status)

    def get_primitive(self, primitive_id: str):
        """Get primitive by ID."""
        return self.registry.get(primitive_id)

    def validate_plan(self, plan_data: dict):
        """Validate a plan."""
        from maicrosoft.core.models import Plan
        plan = Plan.model_validate(plan_data)
        return self.validator.validate(plan)

    def compile_plan(self, plan_data: dict):
        """Compile plan to N8N workflow."""
        from maicrosoft.core.models import Plan
        plan = Plan.model_validate(plan_data)
        return self.compiler.compile(plan)

    def search_primitives(self, query: str, limit: int = 5):
        """Search primitives by query."""
        return self.orchestrator.search_primitives(query, limit)


# Singleton instance
bridge = MaicrosoftBridge()

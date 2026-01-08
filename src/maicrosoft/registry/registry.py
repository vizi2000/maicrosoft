"""Primitive registry for managing and searching primitives."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from maicrosoft.core.models import Particle, Primitive
from maicrosoft.registry.loader import PrimitiveLoader


class PrimitiveRegistry:
    """Registry for managing primitives with search capabilities."""

    def __init__(self, primitives_dir: Path | str | None = None):
        """Initialize registry.

        Args:
            primitives_dir: Path to primitives directory
        """
        self.loader = PrimitiveLoader(primitives_dir)
        self._cache: dict[str, Primitive] = {}

    def get(self, primitive_id: str, use_cache: bool = True) -> Primitive:
        """Get a primitive by ID.

        Args:
            primitive_id: The primitive ID
            use_cache: Whether to use cached version

        Returns:
            The Primitive object
        """
        if use_cache and primitive_id in self._cache:
            return self._cache[primitive_id]

        primitive = self.loader.load_primitive(primitive_id)
        self._cache[primitive_id] = primitive
        return primitive

    def exists(self, primitive_id: str) -> bool:
        """Check if a primitive exists."""
        try:
            self.get(primitive_id)
            return True
        except FileNotFoundError:
            return False

    def list(
        self,
        primitive_type: str | None = None,
        category: str | None = None,
        status: str = "stable",
    ) -> list[dict[str, Any]]:
        """List primitives with filters.

        Args:
            primitive_type: Filter by type
            category: Filter by category
            status: Filter by status (default: stable)

        Returns:
            List of primitive metadata
        """
        return self.loader.list_primitives(
            primitive_type=primitive_type,
            category=category,
            status=status,
        )

    def get_particles(self) -> list[Particle]:
        """Get all stable particles."""
        particles = []
        for entry in self.list(primitive_type="particle", status="stable"):
            try:
                particle = self.get(entry["id"])
                if isinstance(particle, Particle):
                    particles.append(particle)
            except Exception:
                pass
        return particles

    def search_by_tag(self, tag: str) -> list[dict[str, Any]]:
        """Search primitives by tag."""
        results = []
        for entry in self.list(status=None):
            tags = entry.get("tags", [])
            if tag.lower() in [t.lower() for t in tags]:
                results.append(entry)
        return results

    def search_by_name(self, query: str) -> list[dict[str, Any]]:
        """Search primitives by name (partial match)."""
        results = []
        query_lower = query.lower()
        for entry in self.list(status=None):
            name = entry.get("name", "").lower()
            description = entry.get("description", "").lower()
            if query_lower in name or query_lower in description:
                results.append(entry)
        return results

    def get_interface(self, primitive_id: str) -> dict[str, Any]:
        """Get the interface definition for a primitive.

        Args:
            primitive_id: The primitive ID

        Returns:
            Dict with inputs, outputs, errors
        """
        primitive = self.get(primitive_id)
        return {
            "inputs": [inp.model_dump() for inp in primitive.interface.inputs],
            "outputs": [out.model_dump() for out in primitive.interface.outputs],
            "errors": [err.model_dump() for err in primitive.interface.errors],
        }

    def validate_inputs(
        self, primitive_id: str, inputs: dict[str, Any]
    ) -> tuple[bool, list[str]]:
        """Validate inputs against primitive interface.

        Args:
            primitive_id: The primitive ID
            inputs: The input values to validate

        Returns:
            Tuple of (is_valid, list of errors)
        """
        primitive = self.get(primitive_id)
        errors = []

        for inp in primitive.interface.inputs:
            if inp.required and inp.name not in inputs:
                errors.append(f"Missing required input: {inp.name}")
                continue

            if inp.name in inputs:
                value = inputs[inp.name]

                if inp.type.value == "string" and not isinstance(value, str):
                    if not (isinstance(value, str) and value.startswith("{{")):
                        errors.append(
                            f"Input {inp.name} must be string, got {type(value).__name__}"
                        )

                elif inp.type.value == "number" and not isinstance(value, (int, float)):
                    if not (isinstance(value, str) and value.startswith("{{")):
                        errors.append(
                            f"Input {inp.name} must be number, got {type(value).__name__}"
                        )

                elif inp.type.value == "boolean" and not isinstance(value, bool):
                    if not (isinstance(value, str) and value.startswith("{{")):
                        errors.append(
                            f"Input {inp.name} must be boolean, got {type(value).__name__}"
                        )

                elif inp.type.value == "enum" and inp.enum_values:
                    if value not in inp.enum_values:
                        if not (isinstance(value, str) and value.startswith("{{")):
                            errors.append(
                                f"Input {inp.name} must be one of {inp.enum_values}"
                            )

        return len(errors) == 0, errors

    def clear_cache(self) -> None:
        """Clear the primitive cache."""
        self._cache.clear()

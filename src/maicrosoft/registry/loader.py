"""Loader for primitive YAML definitions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from maicrosoft.core.models import Atom, Molecule, Particle, Primitive


class PrimitiveLoader:
    """Loads primitive definitions from YAML files."""

    def __init__(self, primitives_dir: Path | str | None = None):
        """Initialize loader with primitives directory.

        Args:
            primitives_dir: Path to primitives directory. If None, uses default.
        """
        if primitives_dir is None:
            self.primitives_dir = self._find_primitives_dir()
        else:
            self.primitives_dir = Path(primitives_dir)

    def _find_primitives_dir(self) -> Path:
        """Find the primitives directory."""
        candidates = [
            Path(__file__).parent.parent.parent.parent / "primitives",
            Path.cwd() / "primitives",
            Path.home() / ".maicrosoft" / "primitives",
        ]

        for candidate in candidates:
            if candidate.exists() and (candidate / "_meta").exists():
                return candidate

        raise FileNotFoundError(
            "Could not find primitives directory. "
            "Please specify primitives_dir or ensure primitives/ exists."
        )

    def load_yaml(self, path: Path) -> dict[str, Any]:
        """Load a YAML file."""
        with open(path) as f:
            return yaml.safe_load(f)

    def load_registry(self) -> dict[str, Any]:
        """Load the registry.yaml file."""
        registry_path = self.primitives_dir / "_meta" / "registry.yaml"
        return self.load_yaml(registry_path)

    def load_primitive(self, primitive_id: str) -> Primitive:
        """Load a primitive by ID.

        Args:
            primitive_id: The primitive ID (e.g., P001, A001)

        Returns:
            The loaded Primitive object

        Raises:
            FileNotFoundError: If primitive not found
            ValueError: If primitive is invalid
        """
        registry = self.load_registry()

        primitive_type = primitive_id[0]
        type_map = {
            "P": ("particles", Particle),
            "A": ("atoms", Atom),
            "M": ("molecules", Molecule),
            "O": ("organisms", Molecule),
        }

        if primitive_type not in type_map:
            raise ValueError(f"Invalid primitive type: {primitive_type}")

        section_name, model_class = type_map[primitive_type]
        section = registry.get(section_name, [])

        entry = None
        for item in section:
            if item.get("id") == primitive_id:
                entry = item
                break

        if entry is None:
            raise FileNotFoundError(f"Primitive not found: {primitive_id}")

        primitive_path = self.primitives_dir / entry["path"]
        if not primitive_path.exists():
            raise FileNotFoundError(f"Primitive file not found: {primitive_path}")

        data = self.load_yaml(primitive_path)
        return model_class(**data)

    def load_all_particles(self) -> list[Particle]:
        """Load all particles."""
        registry = self.load_registry()
        particles = []

        for entry in registry.get("particles", []):
            try:
                particle = self.load_primitive(entry["id"])
                if isinstance(particle, Particle):
                    particles.append(particle)
            except Exception as e:
                print(f"Warning: Failed to load particle {entry['id']}: {e}")

        return particles

    def load_all_atoms(self) -> list[Atom]:
        """Load all atoms."""
        registry = self.load_registry()
        atoms = []

        for entry in registry.get("atoms", []):
            try:
                atom = self.load_primitive(entry["id"])
                if isinstance(atom, Atom):
                    atoms.append(atom)
            except Exception as e:
                print(f"Warning: Failed to load atom {entry['id']}: {e}")

        return atoms

    def list_primitives(
        self,
        primitive_type: str | None = None,
        category: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """List primitives with optional filters.

        Args:
            primitive_type: Filter by type (particle, atom, molecule, organism)
            category: Filter by category
            status: Filter by status (draft, stable, deprecated)

        Returns:
            List of primitive metadata dicts
        """
        registry = self.load_registry()
        results = []

        sections = {
            "particle": "particles",
            "atom": "atoms",
            "molecule": "molecules",
            "organism": "organisms",
        }

        if primitive_type:
            section_names = [sections.get(primitive_type, primitive_type)]
        else:
            section_names = list(sections.values())

        for section_name in section_names:
            for entry in registry.get(section_name, []):
                if category and entry.get("category") != category:
                    continue
                if status and entry.get("status") != status:
                    continue
                results.append(entry)

        return results

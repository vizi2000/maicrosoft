"""Tests for particle loading and validation."""

import pytest
from pathlib import Path

from maicrosoft.registry.loader import PrimitiveLoader
from maicrosoft.registry.registry import PrimitiveRegistry
from maicrosoft.core.models import Particle


class TestPrimitiveLoader:
    """Tests for PrimitiveLoader."""

    @pytest.fixture
    def loader(self) -> PrimitiveLoader:
        """Create a loader with the test primitives directory."""
        primitives_dir = Path(__file__).parent.parent / "primitives"
        return PrimitiveLoader(primitives_dir)

    def test_load_registry(self, loader: PrimitiveLoader) -> None:
        """Test loading the registry."""
        registry = loader.load_registry()
        assert "particles" in registry
        assert len(registry["particles"]) == 10

    def test_load_particle(self, loader: PrimitiveLoader) -> None:
        """Test loading a specific particle."""
        particle = loader.load_primitive("P001")
        assert isinstance(particle, Particle)
        assert particle.metadata.id == "P001"
        assert particle.metadata.name == "http_call"

    def test_load_all_particles(self, loader: PrimitiveLoader) -> None:
        """Test loading all particles."""
        particles = loader.load_all_particles()
        assert len(particles) == 10

    def test_list_primitives(self, loader: PrimitiveLoader) -> None:
        """Test listing primitives with filters."""
        all_primitives = loader.list_primitives()
        assert len(all_primitives) >= 10

        data_primitives = loader.list_primitives(category="data")
        assert len(data_primitives) >= 2


class TestPrimitiveRegistry:
    """Tests for PrimitiveRegistry."""

    @pytest.fixture
    def registry(self) -> PrimitiveRegistry:
        """Create a registry with test primitives."""
        primitives_dir = Path(__file__).parent.parent / "primitives"
        return PrimitiveRegistry(primitives_dir)

    def test_get_particle(self, registry: PrimitiveRegistry) -> None:
        """Test getting a particle."""
        particle = registry.get("P001")
        assert particle.metadata.name == "http_call"

    def test_exists(self, registry: PrimitiveRegistry) -> None:
        """Test checking if primitive exists."""
        assert registry.exists("P001") is True
        assert registry.exists("P999") is False

    def test_validate_inputs(self, registry: PrimitiveRegistry) -> None:
        """Test input validation."""
        is_valid, errors = registry.validate_inputs(
            "P001",
            {"method": "GET", "url": "https://example.com"},
        )
        assert is_valid is True
        assert len(errors) == 0

        is_valid, errors = registry.validate_inputs("P001", {})
        assert is_valid is False
        assert len(errors) > 0

    def test_search_by_name(self, registry: PrimitiveRegistry) -> None:
        """Test searching by name."""
        results = registry.search_by_name("http")
        assert len(results) >= 1
        assert any(r["id"] == "P001" for r in results)


class TestParticleSchema:
    """Tests for particle schema validation."""

    @pytest.fixture
    def registry(self) -> PrimitiveRegistry:
        """Create a registry."""
        primitives_dir = Path(__file__).parent.parent / "primitives"
        return PrimitiveRegistry(primitives_dir)

    def test_all_particles_have_required_fields(self, registry: PrimitiveRegistry) -> None:
        """Test that all particles have required metadata."""
        particles = registry.get_particles()
        for particle in particles:
            assert particle.metadata.id is not None
            assert particle.metadata.name is not None
            assert particle.metadata.version is not None
            assert particle.metadata.status is not None
            assert particle.metadata.description is not None

    def test_all_particles_have_interface(self, registry: PrimitiveRegistry) -> None:
        """Test that all particles have interface definitions."""
        particles = registry.get_particles()
        for particle in particles:
            assert particle.interface is not None
            assert particle.interface.inputs is not None
            assert particle.interface.outputs is not None

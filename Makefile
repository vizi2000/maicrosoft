.PHONY: install test lint format clean dev

# Install the package
install:
	pip install -e .

# Install with dev dependencies
dev:
	pip install -e ".[dev]"

# Run tests
test:
	PYTHONPATH=src pytest tests/ -v

# Run linting
lint:
	ruff check src/ tests/
	mypy src/

# Format code
format:
	black src/ tests/
	ruff check --fix src/ tests/

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name "*.pyc" -delete

# Validate primitives
validate-primitives:
	PYTHONPATH=src python -c "from maicrosoft.registry import PrimitiveRegistry; r = PrimitiveRegistry(); print(f'Loaded {len(r.get_particles())} particles')"

# Show available particles
particles:
	PYTHONPATH=src python -m maicrosoft.cli particles

# Run the CLI
cli:
	PYTHONPATH=src python -m maicrosoft.cli $(ARGS)

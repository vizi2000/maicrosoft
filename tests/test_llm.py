"""Tests for the LLM orchestrator."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from maicrosoft.llm.orchestrator import LLMOrchestrator, CompositionResult
from maicrosoft.registry import PrimitiveRegistry


@pytest.fixture
def registry():
    """Get primitive registry."""
    return PrimitiveRegistry()


@pytest.fixture
def orchestrator(registry):
    """Get LLM orchestrator."""
    return LLMOrchestrator(registry=registry)


class TestLLMOrchestrator:
    """Tests for LLM orchestrator."""

    def test_build_primitives_list(self, orchestrator):
        """Test building primitives list for prompt."""
        primitives_list = orchestrator._build_primitives_list()

        assert "P001" in primitives_list
        assert "http_call" in primitives_list
        assert "P010" in primitives_list
        assert "log" in primitives_list

    def test_extract_yaml_from_code_block(self, orchestrator):
        """Test extracting YAML from code block."""
        response = '''Here is the plan:

```yaml
metadata:
  id: test
  name: Test
nodes: []
```

Done!'''

        yaml_content = orchestrator._extract_yaml_from_response(response)
        assert yaml_content.startswith("metadata:")
        assert "nodes: []" in yaml_content

    def test_extract_yaml_plain(self, orchestrator):
        """Test extracting YAML without code block."""
        response = '''metadata:
  id: test
  name: Test
nodes: []'''

        yaml_content = orchestrator._extract_yaml_from_response(response)
        assert yaml_content.startswith("metadata:")

    def test_detect_gaps(self, orchestrator):
        """Test detecting gap comments."""
        response = '''metadata:
  id: test
nodes:
  - id: step1
    # GAP: need primitive for email sending
    # GAP: need primitive for SMS notifications
'''

        gaps = orchestrator._detect_gaps(response)
        assert len(gaps) == 2
        assert "email sending" in gaps[0]
        assert "SMS notifications" in gaps[1]

    def test_detect_gaps_none(self, orchestrator):
        """Test detecting gaps when none present."""
        response = '''metadata:
  id: test
nodes:
  - id: step1
    primitive_id: P001
'''

        gaps = orchestrator._detect_gaps(response)
        assert len(gaps) == 0

    def test_search_primitives(self, orchestrator):
        """Test searching for primitives."""
        results = orchestrator.search_primitives("http request api")

        assert len(results) > 0
        # P001 (http_call) should rank highly
        assert results[0]["id"] == "P001"

    def test_search_primitives_database(self, orchestrator):
        """Test searching for database primitives."""
        results = orchestrator.search_primitives("database query sql")

        assert len(results) > 0
        ids = [r["id"] for r in results]
        assert "P002" in ids  # db_query

    def test_search_primitives_limit(self, orchestrator):
        """Test search result limit."""
        results = orchestrator.search_primitives("data", limit=3)
        assert len(results) <= 3

    def test_suggest_primitives(self, orchestrator):
        """Test suggesting primitives for a task."""
        results = orchestrator.suggest_primitives("http request api call")

        assert len(results) > 0
        ids = [r["id"] for r in results]
        assert "P001" in ids  # http_call

    @pytest.mark.asyncio
    async def test_compose_success(self, orchestrator):
        """Test successful plan composition with mocked LLM."""
        valid_yaml = '''metadata:
  id: test-plan-001
  name: Test Plan
  version: "1.0.0"
settings:
  allow_fallback: false
  risk_level: low
trigger:
  type: manual
  config: {}
nodes:
  - id: fetch
    primitive_id: P001
    inputs:
      method: GET
      url: https://api.example.com/data
edges: []'''

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = f"```yaml\n{valid_yaml}\n```"

        with patch("litellm.acompletion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response

            result = await orchestrator.compose("Fetch data from an API")

            assert result.success is True
            assert result.plan is not None
            assert result.plan.metadata.id == "test-plan-001"

    @pytest.mark.asyncio
    async def test_compose_with_gaps(self, orchestrator):
        """Test composition with gap detection."""
        yaml_with_gaps = '''metadata:
  id: test-plan
  name: Test
  version: "1.0.0"
settings:
  allow_fallback: false
trigger:
  type: manual
nodes:
  - id: fetch
    primitive_id: P001
    inputs:
      method: GET
      url: https://api.example.com
    # GAP: need email primitive
edges: []'''

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = f"```yaml\n{yaml_with_gaps}\n```"

        with patch("litellm.acompletion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response

            result = await orchestrator.compose("Fetch data and send email")

            # Plan should still be valid
            assert result.success is True
            # But gaps should be detected
            assert len(result.gaps) > 0
            assert "email" in result.gaps[0].lower()

    @pytest.mark.asyncio
    async def test_compose_invalid_primitive(self, orchestrator):
        """Test composition with invalid primitive ID."""
        invalid_yaml = '''metadata:
  id: test-plan
  name: Test
  version: "1.0.0"
settings:
  allow_fallback: false
trigger:
  type: manual
nodes:
  - id: step1
    primitive_id: P999
    inputs: {}
edges: []'''

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = f"```yaml\n{invalid_yaml}\n```"

        with patch("litellm.acompletion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response

            result = await orchestrator.compose("Do something")

            assert result.success is False
            assert len(result.validation_errors) > 0

    @pytest.mark.asyncio
    async def test_compose_llm_error(self, orchestrator):
        """Test handling LLM errors."""
        with patch("litellm.acompletion", new_callable=AsyncMock) as mock_llm:
            mock_llm.side_effect = Exception("API Error")

            result = await orchestrator.compose("Test task")

            assert result.success is False
            assert "LLM call failed" in result.validation_errors[0]

    def test_compose_sync(self, orchestrator):
        """Test synchronous compose wrapper."""
        valid_yaml = '''metadata:
  id: sync-test
  name: Sync Test
  version: "1.0.0"
settings:
  allow_fallback: false
trigger:
  type: manual
nodes:
  - id: log
    primitive_id: P010
    inputs:
      level: info
      message: test
edges: []'''

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = f"```yaml\n{valid_yaml}\n```"

        with patch("litellm.acompletion", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response

            result = orchestrator.compose_sync("Log a message")

            assert result.success is True
            assert result.plan is not None


class TestCompositionResult:
    """Tests for CompositionResult model."""

    def test_success_result(self):
        """Test successful composition result."""
        result = CompositionResult(
            success=True,
            plan_yaml="metadata:\n  id: test",
        )

        assert result.success is True
        assert result.plan_yaml is not None
        assert len(result.validation_errors) == 0

    def test_failure_result(self):
        """Test failed composition result."""
        result = CompositionResult(
            success=False,
            validation_errors=["Invalid primitive", "Missing input"],
            suggestions=["Check registry"],
        )

        assert result.success is False
        assert len(result.validation_errors) == 2
        assert len(result.suggestions) == 1

    def test_result_with_gaps(self):
        """Test result with gaps."""
        result = CompositionResult(
            success=True,
            gaps=["need email primitive", "need PDF generator"],
        )

        assert result.success is True
        assert len(result.gaps) == 2

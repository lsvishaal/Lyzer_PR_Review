"""Unit tests for LLM client."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.app.llm.client import LLMClient, LLMConfig


class TestLLMConfig:
    """Tests for LLMConfig model."""

    def test_llm_config_creation(self):
        """Test LLMConfig creation with valid data."""
        config = LLMConfig(base_url="http://ollama:11434", model="qwen2.5-coder:3b")
        assert config.base_url == "http://ollama:11434"
        assert config.model == "qwen2.5-coder:3b"

    def test_llm_config_default_values(self):
        """Test LLMConfig with default values."""
        config = LLMConfig()
        assert config.base_url == "http://ollama:11434"
        assert config.model == "qwen2.5-coder:3b"


class TestLLMClient:
    """Tests for LLMClient."""

    @pytest.fixture
    def llm_config(self):
        """Provide test LLM config."""
        return LLMConfig(base_url="http://test:11434", model="test-model")

    @pytest.fixture
    def llm_client(self, llm_config):
        """Provide test LLM client."""
        return LLMClient(config=llm_config)

    def test_llm_client_initialization(self, llm_client, llm_config):
        """Test LLMClient initializes correctly."""
        assert llm_client._config == llm_config
        assert llm_client._client is not None

    @pytest.mark.asyncio
    async def test_generate_success(self, llm_client):
        """Test successful LLM generation."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": "Generated code review"}
        mock_response.raise_for_status = Mock()

        with patch.object(llm_client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await llm_client.generate("Review this code")

            assert result == "Generated code review"
            mock_post.assert_called_once()
            call_kwargs = mock_post.call_args[1]
            assert call_kwargs["json"]["model"] == "test-model"
            assert call_kwargs["json"]["prompt"] == "Review this code"
            assert call_kwargs["json"]["stream"] is False

    @pytest.mark.asyncio
    async def test_generate_with_options(self, llm_client):
        """Test LLM generation with additional options."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": "Response with options"}
        mock_response.raise_for_status = Mock()

        with patch.object(llm_client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await llm_client.generate("Review code", temperature=0.7, max_tokens=500)

            assert result == "Response with options"
            call_kwargs = mock_post.call_args[1]
            assert call_kwargs["json"]["options"]["temperature"] == 0.7
            assert call_kwargs["json"]["options"]["num_predict"] == 500

    @pytest.mark.asyncio
    async def test_generate_empty_response(self, llm_client):
        """Test handling of empty response from LLM."""
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = Mock()

        with patch.object(llm_client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await llm_client.generate("Test prompt")

            assert result == ""

    @pytest.mark.asyncio
    async def test_generate_http_error(self, llm_client):
        """Test handling of HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 500 Error")

        with patch.object(llm_client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(Exception, match="HTTP 500 Error"):
                await llm_client.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_close_client(self, llm_client):
        """Test closing the HTTP client."""
        with patch.object(llm_client._client, "aclose", new_callable=AsyncMock) as mock_close:
            await llm_client.close()
            mock_close.assert_called_once()


class TestFakeLLMClient:
    """Tests for FakeLLMClient (test double)."""

    @pytest.mark.asyncio
    async def test_fake_client_returns_predetermined_response(self):
        """Test FakeLLMClient returns fixed responses."""
        from src.app.llm.client import FakeLLMClient

        fake_client = FakeLLMClient(responses={"test prompt": "test response"})
        result = await fake_client.generate("test prompt")
        assert result == "test response"

    @pytest.mark.asyncio
    async def test_fake_client_default_response(self):
        """Test FakeLLMClient returns default for unknown prompts."""
        from src.app.llm.client import FakeLLMClient

        fake_client = FakeLLMClient()
        result = await fake_client.generate("unknown prompt")
        assert "mock response" in result.lower()

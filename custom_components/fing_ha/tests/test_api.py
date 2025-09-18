"""Test cases for FingApi."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.fing_ha.api import FingApi


class TestFingApi:
    """Test the FingApi class."""

    @pytest.fixture
    def mock_hass(self):
        """Mock HomeAssistant instance."""
        hass = MagicMock()
        hass.async_add_executor_job = AsyncMock()
        return hass

    @pytest.fixture
    def api(self, mock_hass):
        """Create FingApi instance."""
        return FingApi(mock_hass, "localhost", 49090, "test_key")

    def test_init(self, mock_hass):
        """Test initialization."""
        api = FingApi(mock_hass, "host", 443, "key")
        assert api.host == "host"
        assert api.port == 443
        assert api.api_key == "key"
        assert api.hass == mock_hass

    @pytest.mark.asyncio
    async def test_async_get_devices_success(self, api, mock_hass):
        """Test successful get_devices call."""
        mock_result = {"devices": []}
        mock_hass.async_add_executor_job.return_value = mock_result

        result = await api.async_get_devices()
        assert result == mock_result
        mock_hass.async_add_executor_job.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_get_devices_retry_on_timeout(self, api, mock_hass):
        """Test retry on timeout."""
        mock_result = {"devices": []}
        mock_hass.async_add_executor_job.side_effect = [
            asyncio.TimeoutError(),
            mock_result
        ]

        result = await api.async_get_devices()
        assert result == mock_result
        assert mock_hass.async_add_executor_job.call_count == 2

    @pytest.mark.asyncio
    async def test_async_get_devices_max_retries_exceeded(self, api, mock_hass):
        """Test max retries exceeded."""
        mock_hass.async_add_executor_job.side_effect = asyncio.TimeoutError()

        with pytest.raises(RuntimeError, match="Failed to execute API call after .* attempts"):
            await api.async_get_devices()

        assert mock_hass.async_add_executor_job.call_count == 3

    @pytest.mark.asyncio
    async def test_async_get_devices_auth_error_no_retry(self, api, mock_hass):
        """Test auth error raises immediately."""
        mock_hass.async_add_executor_job.side_effect = Exception("401 Unauthorized")

        with pytest.raises(Exception, match="401 Unauthorized"):
            await api.async_get_devices()

        assert mock_hass.async_add_executor_job.call_count == 1

    @pytest.mark.asyncio
    async def test_async_test_connection_success(self, api, mock_hass):
        """Test successful connection test."""
        mock_hass.async_add_executor_job.return_value = {"devices": []}

        result = await api.async_test_connection()
        assert result is True

    @pytest.mark.asyncio
    async def test_async_test_connection_failure(self, api, mock_hass):
        """Test failed connection test."""
        mock_hass.async_add_executor_job.side_effect = Exception("Connection failed")

        result = await api.async_test_connection()
        assert result is False
"""Tests for the Fing API."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fing_agent_api import FingAgent

from custom_components.fing_ha.api import FingApi, INITIAL_BACKOFF, MAX_RETRIES


@pytest.fixture
def mock_hass():
    """Mock Home Assistant."""
    return MagicMock()


@pytest.fixture
def fing_api(mock_hass):
    """Fixture for FingApi."""
    return FingApi(mock_hass, "localhost", 8080, "test_api_key")


def test_init(fing_api, mock_hass):
    """Test the constructor."""
    assert fing_api.hass == mock_hass
    assert fing_api.host == "localhost"
    assert fing_api.port == 8080
    assert fing_api.api_key == "test_api_key"
    assert fing_api._fing is None


def test_get_fing_agent_initialized(fing_api):
    """Test that _get_fing_agent returns the cached instance."""
    mock_agent = MagicMock()
    fing_api._fing = mock_agent
    assert fing_api._get_fing_agent() == mock_agent


@patch("custom_components.fing_ha.api.FingAgent")
@patch("concurrent.futures.ThreadPoolExecutor")
def test_get_fing_agent_initialization(mock_executor, mock_fing_agent_class, fing_api):
    """Test the initialization of FingAgent."""
    mock_agent_instance = MagicMock()
    mock_future = MagicMock()
    mock_future.result.return_value = mock_agent_instance
    mock_submit = mock_executor.return_value.__enter__.return_value.submit
    mock_submit.return_value = mock_future

    agent = fing_api._get_fing_agent()

    # Assert that the executor was used to submit the FingAgent constructor
    mock_submit.assert_called_once_with(
        mock_fing_agent_class, key="test_api_key", ip="localhost", port=8080
    )

    # The FingAgent class should not be called directly in this test
    mock_fing_agent_class.assert_not_called()

    assert agent == mock_agent_instance
    assert fing_api._fing == mock_agent_instance


@pytest.mark.asyncio
async def test_async_call_with_retry_success(fing_api):
    """Test _async_call_with_retry with immediate success."""
    coro_func = AsyncMock(return_value="Success")
    result = await fing_api._async_call_with_retry(coro_func)
    assert result == "Success"
    coro_func.assert_called_once()


@pytest.mark.asyncio
@patch("asyncio.sleep", new_callable=AsyncMock)
async def test_async_call_with_retry_fails_then_succeeds(mock_sleep, fing_api):
    """Test _async_call_with_retry with a single failure."""
    coro_func = AsyncMock(side_effect=[Exception("Network error"), "Success"])
    result = await fing_api._async_call_with_retry(coro_func)
    assert result == "Success"
    assert coro_func.call_count == 2
    mock_sleep.assert_called_once_with(INITIAL_BACKOFF)


@pytest.mark.asyncio
@patch("asyncio.sleep", new_callable=AsyncMock)
async def test_async_call_with_retry_timeout(mock_sleep, fing_api):
    """Test _async_call_with_retry with a timeout."""
    coro_func = AsyncMock(side_effect=asyncio.TimeoutError)
    with pytest.raises(RuntimeError):
        await fing_api._async_call_with_retry(coro_func)
    assert coro_func.call_count == MAX_RETRIES


@pytest.mark.asyncio
async def test_async_call_with_retry_auth_error(fing_api):
    """Test _async_call_with_retry with an auth error."""
    coro_func = AsyncMock(side_effect=Exception("401 Unauthorized"))
    with pytest.raises(Exception, match="401 Unauthorized"):
        await fing_api._async_call_with_retry(coro_func)
    coro_func.assert_called_once()


@pytest.mark.asyncio
@patch("asyncio.sleep", new_callable=AsyncMock)
async def test_async_call_with_retry_max_retries(mock_sleep, fing_api):
    """Test _async_call_with_retry exceeds max retries."""
    coro_func = AsyncMock(side_effect=Exception("API error"))
    with pytest.raises(RuntimeError):
        await fing_api._async_call_with_retry(coro_func)
    assert coro_func.call_count == MAX_RETRIES


@pytest.mark.asyncio
async def test_async_get_devices_async_success(fing_api):
    """Test async_get_devices with an async get_devices method."""
    mock_agent = MagicMock()
    mock_agent.get_devices = AsyncMock(return_value={"devices": []})
    fing_api._fing = mock_agent

    with patch("asyncio.iscoroutinefunction", return_value=True), patch.object(
        fing_api, "_async_call_with_retry", wraps=fing_api._async_call_with_retry
    ) as mock_retry:
        result = await fing_api.async_get_devices()

    assert result == {"devices": []}
    mock_retry.assert_called_once_with(mock_agent.get_devices)


@pytest.mark.asyncio
async def test_async_get_devices_sync_success(fing_api):
    """Test async_get_devices with a sync get_devices method."""
    mock_agent = MagicMock()
    mock_agent.get_devices = MagicMock(return_value={"devices": []})
    fing_api._fing = mock_agent

    with patch("asyncio.iscoroutinefunction", return_value=False):
        result = await fing_api.async_get_devices()

    assert result == {"devices": []}
    mock_agent.get_devices.assert_called_once()


@pytest.mark.asyncio
async def test_async_get_devices_exception(fing_api):
    """Test async_get_devices when an exception occurs."""
    mock_agent = MagicMock()
    mock_agent.get_devices = MagicMock(side_effect=Exception("API Error"))
    fing_api._fing = mock_agent

    with patch("asyncio.iscoroutinefunction", return_value=False), pytest.raises(
        Exception, match="API Error"
    ):
        await fing_api.async_get_devices()


@pytest.mark.asyncio
async def test_async_test_connection_success(fing_api):
    """Test async_test_connection on success."""
    with patch.object(fing_api, "async_get_devices", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {"devices": []}
        assert await fing_api.async_test_connection() is True


@pytest.mark.asyncio
async def test_async_test_connection_failure(fing_api):
    """Test async_test_connection on failure."""
    with patch.object(
        fing_api, "async_get_devices", new_callable=AsyncMock
    ) as mock_get:
        mock_get.side_effect = Exception("Connection failed")
        assert await fing_api.async_test_connection() is False

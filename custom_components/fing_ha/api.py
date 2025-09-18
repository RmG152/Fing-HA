"""Fing API wrapper for Home Assistant."""
from __future__ import annotations

import asyncio
import logging
from typing import Any
import inspect

from fing_agent_api import FingAgent

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# Constants for resilience
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0  # seconds
BACKOFF_FACTOR = 2.0
TIMEOUT = 30.0  # seconds


class FingApi:
    """Wrapper for Fing API interactions."""

    def __init__(self, hass: HomeAssistant, host: str, port: int, api_key: str) -> None:
        """Initialize the Fing API wrapper."""
        self.hass = hass
        self.host = host
        self.port = port
        self.api_key = api_key
        self._fing = None  # Defer initialization to avoid blocking SSL calls

    def _get_fing_agent(self):
        """Get or create FingAgent instance, handling SSL blocking calls."""
        if self._fing is None:
            _LOGGER.debug("Initializing FingAgent with SSL context creation - starting thread pool")
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                _LOGGER.debug("Submitting FingAgent initialization to thread")
                future = executor.submit(FingAgent, key=self.api_key, ip=self.host, port=self.port)
                _LOGGER.debug("Waiting for FingAgent initialization result")
                self._fing = future.result()
                _LOGGER.debug("FingAgent initialized successfully in thread")
        return self._fing

    async def _async_call_with_retry(self, func):
        """Call a (sync or async) function with retry logic, timeouts, and detailed logging.

        func should be a callable with no arguments. This implementation always
        executes the call inside the default executor to avoid any blocking
        operations (like SSL cert loading) on the Home Assistant event loop.
        If the callable returns an awaitable, that awaitable is executed with
        asyncio.run inside the worker thread.
        """
        attempt = 0
        backoff = INITIAL_BACKOFF
        while attempt < MAX_RETRIES:
            try:
                _LOGGER.debug("Attempting API call, attempt %d", attempt + 1)

                loop = asyncio.get_running_loop()

                def _worker_call():
                    # Execute the callable in the thread. If it returns an awaitable,
                    # run it in that thread's own event loop to avoid touching the main loop.
                    res = func()
                    if inspect.isawaitable(res):
                        return asyncio.run(res)
                    return res

                _LOGGER.debug("Running API call in executor to avoid event loop blocking")
                result = await asyncio.wait_for(loop.run_in_executor(None, _worker_call), timeout=TIMEOUT)

                _LOGGER.debug("API call successful on attempt %d", attempt + 1)
                return result
            except asyncio.TimeoutError as err:
                _LOGGER.warning("Timeout on API call (attempt %d): %s", attempt + 1, err)
                error_type = "timeout"
            except Exception as err:
                error_msg = str(err)
                if "401" in error_msg or "unauthorized" in error_msg.lower():
                    _LOGGER.error("Authentication error: %s", error_msg)
                    raise  # Don't retry auth errors
                elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                    _LOGGER.warning("Network error (attempt %d): %s", attempt + 1, error_msg)
                    error_type = "network"
                else:
                    _LOGGER.error("API error (attempt %d): %s", attempt + 1, error_msg)
                    error_type = "api"

            if attempt < MAX_RETRIES - 1:
                _LOGGER.info("Retrying in %.1f seconds", backoff)
                await asyncio.sleep(backoff)
                backoff *= BACKOFF_FACTOR
            attempt += 1

        _LOGGER.error("Max retries exceeded")
        raise RuntimeError(f"Failed to execute API call after {MAX_RETRIES} attempts")

    async def async_get_devices(self) -> dict[str, Any]:
        """Fetch devices from Fing API asynchronously."""
        _LOGGER.debug("Fetching devices from FingAgent - starting async_get_devices")
        try:
            # Get FingAgent instance (handles SSL initialization in thread)
            _LOGGER.debug("Getting FingAgent instance")
            # Ensure the FingAgent creation runs in a worker thread to avoid any
            # SSL/blocking work on the main event loop.
            fing_agent = await self.hass.async_add_executor_job(self._get_fing_agent)
            _LOGGER.debug("FingAgent instance obtained, checking get_devices method type")

            # Always execute the agent method via the retry wrapper which itself
            # runs the call inside an executor worker.
            result = await self._async_call_with_retry(fing_agent.get_devices)

            _LOGGER.debug("FingAgent.get_devices() returned: %s", result)
            _LOGGER.debug("Result type: %s", type(result))
            if hasattr(result, '__dict__'):
                _LOGGER.debug("Result attributes: %s", result.__dict__)

            return result
        except Exception as err:
            _LOGGER.error("Error fetching devices: %s", err)
            raise

    async def async_test_connection(self) -> bool:
        """Test connection to Fing API."""
        try:
            await self.async_get_devices()
            return True
        except Exception as err:
            _LOGGER.debug("Connection test failed: %s", err)
            return False
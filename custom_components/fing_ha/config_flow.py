"""Config flow for Fing HA integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate invalid authentication."""


class FingHAConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Fing HA."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                # Validate connection using Fing library
                from fing_agent_api import FingAgent

                fing = FingAgent(
                    key=user_input["api_key"],
                    ip=user_input["host"],
                    port=user_input.get("port", 49090),
                )
                # Test connectivity by attempting to get devices
                await fing.get_devices()
            except Exception as exc:
                _LOGGER.error("Error connecting to Fing API: %s", exc)
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title="Fing HA",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("host"): str,
                    vol.Optional("port", default=49090): vol.Coerce(int),
                    vol.Required("api_key"): str,
                    vol.Required("scan_interval", default=30): vol.Coerce(int),
                    vol.Optional("enable_notifications", default=False): bool,
                    vol.Optional("exclude_unknown_devices", default=False): bool,
                }
            ),
            errors=errors,
        )
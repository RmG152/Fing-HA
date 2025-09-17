"""Fing HA integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FingApi
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "switch"]  # Add other platforms as needed


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Fing HA from a config entry."""
    _LOGGER.info("Setting up Fing HA integration for entry: %s", entry.entry_id)
    hass.data.setdefault(DOMAIN, {})

    # Initialize the entry data structure early
    hass.data[DOMAIN][entry.entry_id] = {"alert_mode": False, "previous_devices": {}}

    # Initialize API with proper SSL handling
    api = FingApi(
        hass=hass,
        host=entry.data["host"],
        port=entry.data.get("port", 49090),
        api_key=entry.data["api_key"],
    )

    async def async_update_data() -> dict[str, Any]:
        """Fetch data from Fing API with graceful degradation."""
        data = {}

        # Fetch devices directly from Fing API
        try:
            _LOGGER.debug("Starting device fetch from Fing API")
            devices = await api.async_get_devices()
            _LOGGER.debug("Raw devices data: %s", devices)
            _LOGGER.debug("Devices data type: %s", type(devices))
            data["devices"] = devices

            # For large networks, warn if many devices (if countable)
            try:
                if hasattr(devices, '__len__') and len(devices) > 100:
                    _LOGGER.warning("Large network detected: %d devices", len(devices))
                elif hasattr(devices, '__len__'):
                    _LOGGER.info("Fetched %d devices from Fing API", len(devices))
                else:
                    _LOGGER.debug("Device data doesn't support len(), type: %s", type(devices))
            except (TypeError, AttributeError):
                _LOGGER.debug("Device count not available for large network check")
        except Exception as err:
            _LOGGER.error("Failed to fetch devices: %s", err)
            data["devices"] = {}  # Graceful degradation
            raise UpdateFailed(f"Error fetching device data: {err}")

        # Notifications for device events
        if hass.data[DOMAIN][entry.entry_id].get("alert_mode", entry.data.get("enable_notifications", False)):
            previous_devices = hass.data[DOMAIN][entry.entry_id].get("previous_devices", {})
            current_devices = data.get("devices", {})

            # Convert devices to dict if needed for iteration
            try:
                if hasattr(current_devices, 'items'):
                    current_devices_dict = dict(current_devices.items())
                elif hasattr(current_devices, '__iter__') and not isinstance(current_devices, (str, bytes)):
                    current_devices_dict = {str(i): item for i, item in enumerate(current_devices)}
                else:
                    current_devices_dict = {}
            except Exception:
                current_devices_dict = {}

            # New devices
            for device_id, device_data in current_devices_dict.items():
                if device_id not in previous_devices:
                    hass.bus.async_fire(
                        "fing_ha.new_device",
                        {
                            "device_id": device_id,
                            "hostname": getattr(device_data, 'hostname', getattr(device_data, 'get', lambda x: "Unknown")("hostname")) if hasattr(device_data, 'hostname') or hasattr(device_data, 'get') else "Unknown",
                            "mac_address": getattr(device_data, 'mac_address', getattr(device_data, 'get', lambda x: "")("mac_address")) if hasattr(device_data, 'mac_address') or hasattr(device_data, 'get') else "",
                            "ip_address": getattr(device_data, 'ip', getattr(device_data, 'get', lambda x: "")("ip")) if hasattr(device_data, 'ip') or hasattr(device_data, 'get') else "",
                            "vendor": getattr(device_data, 'vendor', getattr(device_data, 'get', lambda x: "Unknown")("vendor")) if hasattr(device_data, 'vendor') or hasattr(device_data, 'get') else "Unknown",
                        }
                    )

            # Update previous devices
            try:
                hass.data[DOMAIN][entry.entry_id]["previous_devices"] = current_devices_dict.copy() if hasattr(current_devices_dict, 'copy') else dict(current_devices_dict)
            except Exception:
                hass.data[DOMAIN][entry.entry_id]["previous_devices"] = {}

        return data

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        config_entry=entry,
        name="Fing HA",
        update_method=async_update_data,
        update_interval=timedelta(seconds=entry.data.get("scan_interval", 30)),
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        _LOGGER.warning("Initial data refresh failed: %s (will retry later)", err)
        # Continue setup even if first refresh fails, allowing recovery on next update

    # Update with API and coordinator, preserving previous devices
    devices = coordinator.data.get("devices", {}) if coordinator.data else {}
    try:
        previous_devices = devices.copy() if hasattr(devices, 'copy') else dict(devices) if hasattr(devices, 'items') else {}
    except Exception:
        previous_devices = {}

    hass.data[DOMAIN][entry.entry_id].update({
        "api": api,
        "coordinator": coordinator,
        "previous_devices": previous_devices
    })

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
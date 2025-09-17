"""Fing HA switch platform."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class FingAlertSwitch(SwitchEntity):
    """Representation of a Fing HA alert switch."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the switch."""
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = f"{DOMAIN}_alert_mode"
        self._attr_name = "Fing HA Alert Mode"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Fing HA",
            manufacturer="Fing",
            model="Integration",
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if alert mode is on."""
        return self.hass.data[DOMAIN][self.entry.entry_id].get(
            "alert_mode", self.entry.data.get("enable_notifications", False)
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        self.hass.data[DOMAIN][self.entry.entry_id]["alert_mode"] = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        self.hass.data[DOMAIN][self.entry.entry_id]["alert_mode"] = False
        self.async_write_ha_state()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fing HA switch platform."""
    entities = [FingAlertSwitch(hass, entry)]
    async_add_entities(entities)
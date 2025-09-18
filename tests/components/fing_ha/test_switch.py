"""Tests for the Fing switch platform."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.fing_ha.const import DOMAIN
from custom_components.fing_ha.switch import FingAlertSwitch, async_setup_entry


@pytest.fixture
def mock_config_entry():
    """Mock a config entry."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.data = {"enable_notifications": True}
    return entry


@pytest.fixture
def setup_hass_data(hass: HomeAssistant, mock_config_entry):
    """Set up hass.data for the tests."""
    hass.data[DOMAIN] = {mock_config_entry.entry_id: {}}


def test_switch_init(hass: HomeAssistant, mock_config_entry):
    """Test the FingAlertSwitch constructor."""
    switch = FingAlertSwitch(hass, mock_config_entry)
    assert switch.unique_id == f"{DOMAIN}_alert_mode"
    assert switch.name == "Fing HA Alert Mode"


@pytest.mark.usefixtures("setup_hass_data")
def test_switch_is_on(hass: HomeAssistant, mock_config_entry):
    """Test the is_on property of the switch."""
    switch = FingAlertSwitch(hass, mock_config_entry)

    # Test fallback to entry data
    assert switch.is_on is True

    # Test when alert_mode is True in hass.data
    hass.data[DOMAIN][mock_config_entry.entry_id]["alert_mode"] = True
    assert switch.is_on is True

    # Test when alert_mode is False in hass.data
    hass.data[DOMAIN][mock_config_entry.entry_id]["alert_mode"] = False
    assert switch.is_on is False


@pytest.mark.asyncio
@pytest.mark.usefixtures("setup_hass_data")
async def test_switch_turn_on(hass: HomeAssistant, mock_config_entry):
    """Test the async_turn_on method."""
    switch = FingAlertSwitch(hass, mock_config_entry)
    switch.async_write_ha_state = MagicMock()

    await switch.async_turn_on()

    assert hass.data[DOMAIN][mock_config_entry.entry_id]["alert_mode"] is True
    switch.async_write_ha_state.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.usefixtures("setup_hass_data")
async def test_switch_turn_off(hass: HomeAssistant, mock_config_entry):
    """Test the async_turn_off method."""
    switch = FingAlertSwitch(hass, mock_config_entry)
    switch.async_write_ha_state = MagicMock()

    await switch.async_turn_off()

    assert hass.data[DOMAIN][mock_config_entry.entry_id]["alert_mode"] is False
    switch.async_write_ha_state.assert_called_once()


@pytest.mark.asyncio
async def test_async_setup_entry(hass: HomeAssistant, mock_config_entry):
    """Test the switch platform's setup."""
    async_add_entities = MagicMock()

    await async_setup_entry(hass, mock_config_entry, async_add_entities)

    async_add_entities.assert_called_once()
    assert isinstance(async_add_entities.call_args.args[0][0], FingAlertSwitch)

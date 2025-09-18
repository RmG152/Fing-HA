"""Tests for the Fing sensor platform."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from custom_components.fing_ha.const import DOMAIN
from custom_components.fing_ha.sensor import (
    FingDeviceBinarySensor,
    FingDeviceSensor,
    async_setup_entry,
)


@pytest.fixture
def mock_coordinator():
    """Mock a an update coordinator."""
    coordinator = MagicMock(spec=DataUpdateCoordinator)
    coordinator.data = {}
    return coordinator


@pytest.fixture
def mock_device_data():
    """Mock device data."""
    return {
        "mac_address": "00:11:22:33:44:55",
        "hostname": "TestDevice",
        "vendor": "TestVendor",
        "device_type": "TestType",
    }


def test_binary_sensor_init(mock_coordinator, mock_device_data):
    """Test the FingDeviceBinarySensor constructor."""
    sensor = FingDeviceBinarySensor(mock_coordinator, "00:11:22:33:44:55", mock_device_data)
    assert sensor.unique_id == f"{DOMAIN}_00:11:22:33:44:55_online"
    assert sensor.name == "TestDevice (4455) Online"
    assert sensor.device_class == "presence"


def test_sensor_init(mock_coordinator, mock_device_data):
    """Test the FingDeviceSensor constructor."""
    sensor = FingDeviceSensor(
        mock_coordinator, "00:11:22:33:44:55", mock_device_data, "ip"
    )
    assert sensor.unique_id == f"{DOMAIN}_00:11:22:33:44:55_ip"
    assert sensor.name == "TestDevice (4455) IP Address"


class MockFingDevice:
    """Mock Fing device from fing-agent-api."""

    def __init__(self, mac, state="UP", ip="192.168.1.1", first_seen=None):
        self.mac_address = mac
        self.ip_address = ip
        self.first_seen = first_seen
        self._device_json = {
            "mac": mac,
            "state": state,
            "ip": [ip],
            "first_seen": first_seen,
        }


class MockDeviceResponse:
    """Mock DeviceResponse from fing-agent-api."""

    def __init__(self, devices):
        self._devices = devices


@pytest.mark.parametrize(
    "coordinator_data, device_id, expected_is_on",
    [
        ({}, "any_id", False),
        ({"devices": None}, "any_id", False),
        (
            {"devices": {"00:11:22:33:44:55": {"online": True}}},
            "00:11:22:33:44:55",
            True,
        ),
        (
            {"devices": {"00:11:22:33:44:55": {"online": False}}},
            "00:11:22:33:44:55",
            False,
        ),
        ({"devices": {"another_id": {"online": True}}}, "00:11:22:33:44:55", False),
        (
            {
                "devices": MockDeviceResponse(
                    [MockFingDevice(mac="00:11:22:33:44:55", state="UP")]
                )
            },
            "00:11:22:33:44:55",
            True,
        ),
        (
            {
                "devices": MockDeviceResponse(
                    [MockFingDevice(mac="00:11:22:33:44:55", state="DOWN")]
                )
            },
            "00:11:22:33:44:55",
            False,
        ),
    ],
)
def test_binary_sensor_is_on(
    mock_coordinator, mock_device_data, coordinator_data, device_id, expected_is_on
):
    """Test the is_on property of the binary sensor."""
    mock_coordinator.data = coordinator_data
    sensor = FingDeviceBinarySensor(mock_coordinator, device_id, mock_device_data)
    assert sensor.is_on is expected_is_on


@pytest.mark.parametrize(
    "coordinator_data, device_id, sensor_type, expected_value",
    [
        ({}, "any_id", "ip", None),
        ({"devices": None}, "any_id", "ip", None),
        (
            {"devices": {"00:11:22:33:44:55": {"ip": "192.168.1.1"}}},
            "00:11:22:33:44:55",
            "ip",
            "192.168.1.1",
        ),
        (
            {
                "devices": {
                    "00:11:22:33:44:55": {
                        "first_seen": "2023-01-01T00:00:00.000Z"
                    }
                }
            },
            "00:11:22:33:44:55",
            "first_seen",
            datetime(2023, 1, 1, 0, 0, tzinfo=timezone.utc),
        ),
        (
            {"devices": {"another_id": {"ip": "192.168.1.2"}}},
            "00:11:22:33:44:55",
            "ip",
            None,
        ),
        (
            {
                "devices": MockDeviceResponse(
                    [MockFingDevice(mac="00:11:22:33:44:55", ip="192.168.1.10")]
                )
            },
            "00:11:22:33:44:55",
            "ip",
            "192.168.1.10",
        ),
    ],
)
def test_sensor_native_value(
    mock_coordinator,
    mock_device_data,
    coordinator_data,
    device_id,
    sensor_type,
    expected_value,
):
    """Test the native_value property of the sensor."""
    mock_coordinator.data = coordinator_data
    sensor = FingDeviceSensor(mock_coordinator, device_id, mock_device_data, sensor_type)

    # The native_value property for timestamps converts string to datetime object
    if isinstance(expected_value, str) and expected_value.endswith("Z"):
        with patch("homeassistant.util.dt.utcnow", return_value=datetime(2023, 1, 1, tzinfo=timezone.utc)):
             # We need to parse the string to a datetime object for comparison
            parsed_datetime = dt_util.parse_datetime(expected_value)
            assert sensor.native_value == parsed_datetime
    else:
        assert sensor.native_value == expected_value


@pytest.mark.asyncio
async def test_async_setup_entry(hass: HomeAssistant):
    """Test the sensor platform's setup."""
    config_entry = MagicMock()
    config_entry.entry_id = "test_entry_id"
    config_entry.data = {}

    # Mock the coordinator and api
    mock_coordinator = MagicMock(spec=DataUpdateCoordinator)
    mock_coordinator.data = {
        "devices": {
            "00:11:22:33:44:55": {
                "mac_address": "00:11:22:33:44:55",
                "hostname": "TestDevice",
                "vendor": "TestVendor",
                "device_type": "TestType",
                "online": True,
                "ip": "192.168.1.100",
                "first_seen": "2023-01-01T00:00:00.000Z",
                "last_changed": "2023-01-01T01:00:00.000Z",
            }
        }
    }

    hass.data[DOMAIN] = {
        "test_entry_id": {"coordinator": mock_coordinator, "previous_devices": {}}
    }

    async_add_entities = MagicMock()

    with patch(
        "custom_components.fing_ha.sensor._prepare_entities_sync"
    ) as mock_prepare:
        mock_prepare.return_value = []
        await async_setup_entry(hass, config_entry, async_add_entities)

        # Give time for async_create_task to run
        await hass.async_block_till_done()

        mock_prepare.assert_called_once()
        async_add_entities.assert_called_once_with([])

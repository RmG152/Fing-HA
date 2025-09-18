"""Tests for the Fing sensor platform."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from custom_components.fing_ha.const import DOMAIN
from custom_components.fing_ha.sensor import (
    FingAgentSensor,
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


@pytest.fixture
def mock_hass():
    """Mock Home Assistant."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {
        DOMAIN: {
            "test_entry_id": {
                "alert_mode": True,
                "coordinator": None,
                "previous_devices": {}
            }
        }
    }
    return hass


@pytest.fixture
def mock_config_entry():
    """Mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    entry.data = {}
    return entry


@pytest.fixture
def mock_agent_info():
    """Mock agent info data."""
    return {
        "ip": "192.168.1.100",
        "model_name": "Fing Agent Pro",
        "state": "running",
        "agent_id": "agent-123",
        "friendly_name": "My Fing Agent",
        "device_type": "Agent",
        "manufacturer": "Fing",
    }


class MockAgentInfoObject:
    """Mock AgentInfo object from Fing API."""
    def __init__(self):
        # Private attributes as stored in the actual object
        self._ip = "192.168.1.101"
        self._ip_address = "192.168.1.102"  # Alternative key
        self._model_name = "Fing Agent Plus"
        self._model = "Fing Agent Basic"  # Alternative key
        self._agent_state = "online"
        self._agent_id = "agent-456"
        self._id = "agent-789"  # Alternative key
        self._friendly_name = "Agent Name"
        self._name = "Alternative Name"  # Alternative key
        self._device_type = "Network Agent"
        self._type = "Agent Type"  # Alternative key
        self._manufacturer = "Fing Corp"
        self._vendor = "Fing Inc"  # Alternative key

    # Properties to match the actual AgentInfoResponse
    @property
    def ip(self):
        return self._ip

    @property
    def ip_address(self):
        return self._ip_address

    @property
    def model_name(self):
        return self._model_name

    @property
    def model(self):
        return self._model

    @property
    def state(self):
        return self._agent_state

    @property
    def agent_id(self):
        return self._agent_id

    @property
    def id(self):
        return self._id

    @property
    def friendly_name(self):
        return self._friendly_name

    @property
    def name(self):
        return self._name

    @property
    def device_type(self):
        return self._device_type

    @property
    def type(self):
        return self._type

    @property
    def manufacturer(self):
        return self._manufacturer

    @property
    def vendor(self):
        return self._vendor


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


def test_agent_sensor_init(mock_hass, mock_config_entry, mock_coordinator):
    """Test the FingAgentSensor constructor."""
    sensor = FingAgentSensor(mock_hass, mock_config_entry, mock_coordinator, "ip")
    assert sensor.unique_id == f"{DOMAIN}_agent_ip"
    assert sensor.name == "Fing Agent IP Address"
    assert sensor.hass == mock_hass
    assert sensor.entry == mock_config_entry
    assert sensor.coordinator == mock_coordinator
    assert sensor.sensor_type == "ip"


@pytest.mark.parametrize(
    "sensor_type, expected_name",
    [
        ("ip", "Fing Agent IP Address"),
        ("model_name", "Fing Agent Model Name"),
        ("state", "Fing Agent State"),
        ("agent_id", "Fing Agent ID"),
        ("friendly_name", "Fing Agent Friendly Name"),
        ("device_type", "Fing Agent Device Type"),
        ("manufacturer", "Fing Agent Manufacturer"),
    ],
)
def test_agent_sensor_names(mock_hass, mock_config_entry, mock_coordinator, sensor_type, expected_name):
    """Test agent sensor names for all types."""
    sensor = FingAgentSensor(mock_hass, mock_config_entry, mock_coordinator, sensor_type)
    assert sensor.name == expected_name


@pytest.mark.parametrize(
    "coordinator_data, sensor_type, expected_value",
    [
        # Test with dict agent_info
        ({"agent_info": {"ip": "192.168.1.100"}}, "ip", "192.168.1.100"),
        ({"agent_info": {"model_name": "Fing Pro"}}, "model_name", "Fing Pro"),
        ({"agent_info": {"state": "running"}}, "state", "running"),
        ({"agent_info": {"agent_id": "agent-123"}}, "agent_id", "agent-123"),
        ({"agent_info": {"friendly_name": "My Agent"}}, "friendly_name", "My Agent"),
        ({"agent_info": {"device_type": "Agent"}}, "device_type", "Agent"),
        ({"agent_info": {"manufacturer": "Fing"}}, "manufacturer", "Fing"),
        # Test with alternative keys in dict
        ({"agent_info": {"ip_address": "192.168.1.101"}}, "ip", "192.168.1.101"),
        ({"agent_info": {"model": "Fing Basic"}}, "model_name", "Fing Basic"),
        ({"agent_info": {"id": "agent-456"}}, "agent_id", "agent-456"),
        ({"agent_info": {"name": "Alt Name"}}, "friendly_name", "Alt Name"),
        ({"agent_info": {"type": "Alt Type"}}, "device_type", "Alt Type"),
        ({"agent_info": {"vendor": "Fing Inc"}}, "manufacturer", "Fing Inc"),
        # Test with MockAgentInfoObject
        ({"agent_info": MockAgentInfoObject()}, "ip", "192.168.1.101"),
        ({"agent_info": MockAgentInfoObject()}, "model_name", "Fing Agent Plus"),
        ({"agent_info": MockAgentInfoObject()}, "state", "online"),
        ({"agent_info": MockAgentInfoObject()}, "agent_id", "agent-456"),
        ({"agent_info": MockAgentInfoObject()}, "friendly_name", "Agent Name"),
        ({"agent_info": MockAgentInfoObject()}, "device_type", "Network Agent"),
        ({"agent_info": MockAgentInfoObject()}, "manufacturer", "Fing Corp"),
        # Test with alternative keys in object
        ({"agent_info": MockAgentInfoObject()}, "ip", "192.168.1.101"),  # Uses primary
        # Test missing data
        ({}, "ip", None),
        ({"agent_info": None}, "ip", None),
        ({"agent_info": {}}, "ip", None),
    ],
)
def test_agent_sensor_native_value(
    mock_hass, mock_config_entry, mock_coordinator, coordinator_data, sensor_type, expected_value
):
    """Test the native_value property of agent sensors."""
    mock_coordinator.data = coordinator_data
    sensor = FingAgentSensor(mock_hass, mock_config_entry, mock_coordinator, sensor_type)
    assert sensor.native_value == expected_value


@pytest.mark.parametrize(
    "alert_mode, expected_available",
    [
        (True, True),
        (False, False),
    ],
)
def test_agent_sensor_available(mock_hass, mock_config_entry, mock_coordinator, alert_mode, expected_available):
    """Test the available property of agent sensors with different alert_mode settings."""
    # Mock the coordinator's available property
    mock_coordinator.available = True

    # Set alert_mode in hass data
    mock_hass.data[DOMAIN][mock_config_entry.entry_id]["alert_mode"] = alert_mode

    sensor = FingAgentSensor(mock_hass, mock_config_entry, mock_coordinator, "ip")
    assert sensor.available == expected_available


def test_agent_sensor_available_coordinator_unavailable(mock_hass, mock_config_entry, mock_coordinator):
    """Test the available property when coordinator is unavailable."""
    mock_coordinator.available = False
    mock_hass.data[DOMAIN][mock_config_entry.entry_id]["alert_mode"] = True

    sensor = FingAgentSensor(mock_hass, mock_config_entry, mock_coordinator, "ip")
    assert sensor.available == False


def test_agent_sensor_native_value_with_custom_attribute(mock_hass, mock_config_entry, mock_coordinator):
    """Test native_value with a custom sensor_type that uses getattr fallback."""
    mock_coordinator.data = {"agent_info": MockAgentInfoObject()}

    # Add a custom attribute
    mock_coordinator.data["agent_info"].custom_attr = "custom_value"

    sensor = FingAgentSensor(mock_hass, mock_config_entry, mock_coordinator, "custom_attr")
    assert sensor.native_value == "custom_value"


def test_agent_sensor_native_value_missing_entry_data(mock_hass, mock_config_entry, mock_coordinator):
    """Test native_value when entry data is missing."""
    # Remove the entry from hass.data
    del mock_hass.data[DOMAIN][mock_config_entry.entry_id]

    sensor = FingAgentSensor(mock_hass, mock_config_entry, mock_coordinator, "ip")

    # Should handle gracefully without crashing
    assert sensor.available == False

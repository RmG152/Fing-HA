"""Test cases for Fing sensor entities."""
from unittest.mock import MagicMock

import pytest

from custom_components.fing_ha.sensor import FingDeviceBinarySensor, FingDeviceSensor


class TestFingDeviceBinarySensor:
    """Test the FingDeviceBinarySensor class."""

    @pytest.fixture
    def mock_coordinator(self):
        """Mock coordinator."""
        coordinator = MagicMock()
        coordinator.data = {
            "devices": {
                "device1": {"online": True, "mac_address": "00:11:22:33:44:55", "hostname": "Device1"}
            }
        }
        return coordinator

    @pytest.fixture
    def device_data(self):
        """Sample device data."""
        return {
            "mac_address": "00:11:22:33:44:55",
            "hostname": "Device1",
            "vendor": "Vendor",
            "device_type": "Type"
        }

    def test_init(self, mock_coordinator, device_data):
        """Test initialization."""
        sensor = FingDeviceBinarySensor(mock_coordinator, "device1", device_data)
        assert sensor.device_id == "device1"
        assert sensor._device_data == device_data
        assert sensor.unique_id == "fing_ha_00:11:22:33:44:55_online"
        assert sensor.name == "Device1 Online"
        assert sensor.device_class == "connectivity"

    def test_is_on(self, mock_coordinator, device_data):
        """Test is_on property."""
        sensor = FingDeviceBinarySensor(mock_coordinator, "device1", device_data)
        assert sensor.is_on is True

    def test_is_on_device_not_found(self, mock_coordinator, device_data):
        """Test is_on when device not in coordinator data."""
        mock_coordinator.data = {"devices": {}}
        sensor = FingDeviceBinarySensor(mock_coordinator, "device1", device_data)
        assert sensor.is_on is None


class TestFingDeviceSensor:
    """Test the FingDeviceSensor class."""

    @pytest.fixture
    def mock_coordinator(self):
        """Mock coordinator."""
        coordinator = MagicMock()
        coordinator.data = {
            "devices": {
                "device1": {
                    "ip": "192.168.1.100",
                    "first_seen": "2023-01-01T10:00:00Z",
                    "last_changed": "2023-12-01T15:30:00Z",
                    "mac_address": "00:11:22:33:44:55",
                    "hostname": "Device1"
                }
            }
        }
        return coordinator

    @pytest.fixture
    def device_data(self):
        """Sample device data."""
        return {
            "mac_address": "00:11:22:33:44:55",
            "hostname": "Device1",
            "vendor": "Vendor",
            "device_type": "Type"
        }

    def test_init_ip_sensor(self, mock_coordinator, device_data):
        """Test initialization of IP sensor."""
        sensor = FingDeviceSensor(mock_coordinator, "device1", device_data, "ip")
        assert sensor.device_id == "device1"
        assert sensor.sensor_type == "ip"
        assert sensor.unique_id == "fing_ha_00:11:22:33:44:55_ip"
        assert sensor.name == "Device1 Ip"
        assert sensor.device_class == "ip_address"

    def test_init_first_seen_sensor(self, mock_coordinator, device_data):
        """Test initialization of first_seen sensor."""
        sensor = FingDeviceSensor(mock_coordinator, "device1", device_data, "first_seen")
        assert sensor.device_class == "timestamp"
        assert sensor.state_class is None

    def test_init_last_changed_sensor(self, mock_coordinator, device_data):
        """Test initialization of last_changed sensor."""
        sensor = FingDeviceSensor(mock_coordinator, "device1", device_data, "last_changed")
        assert sensor.device_class == "timestamp"
        assert sensor.state_class is None

    def test_native_value_ip(self, mock_coordinator, device_data):
        """Test native_value for IP sensor."""
        sensor = FingDeviceSensor(mock_coordinator, "device1", device_data, "ip")
        assert sensor.native_value == "192.168.1.100"

    def test_native_value_first_seen(self, mock_coordinator, device_data):
        """Test native_value for first_seen sensor."""
        sensor = FingDeviceSensor(mock_coordinator, "device1", device_data, "first_seen")
        assert sensor.native_value is not None
        # Should be parsed as datetime
        from datetime import datetime
        assert isinstance(sensor.native_value, datetime)

    def test_native_value_last_changed(self, mock_coordinator, device_data):
        """Test native_value for last_changed sensor."""
        sensor = FingDeviceSensor(mock_coordinator, "device1", device_data, "last_changed")
        assert sensor.native_value is not None
        # Should be parsed as datetime
        from datetime import datetime
        assert isinstance(sensor.native_value, datetime)

    def test_native_value_device_not_found(self, mock_coordinator, device_data):
        """Test native_value when device not in coordinator data."""
        mock_coordinator.data = {"devices": {}}
        sensor = FingDeviceSensor(mock_coordinator, "device1", device_data, "ip")
        assert sensor.native_value is None
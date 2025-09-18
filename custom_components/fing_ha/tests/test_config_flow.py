"""Test cases for FingHAConfigFlow."""
from unittest.mock import MagicMock, patch

import pytest
from voluptuous import Invalid

from custom_components.fing_ha.config_flow import (
    CannotConnect,
    FingHAConfigFlow,
    InvalidAuth,
)


class TestFingHAConfigFlow:
    """Test the FingHAConfigFlow class."""

    @pytest.fixture
    def config_flow(self):
        """Create config flow instance."""
        flow = FingHAConfigFlow()
        flow.hass = MagicMock()
        return flow

    @pytest.mark.asyncio
    async def test_step_user_success(self, config_flow):
        """Test successful user step."""
        user_input = {
            "host": "localhost",
            "port": 49090,
            "api_key": "test_key",
            "scan_interval": 30,
            "enable_notifications": True,
            "exclude_unknown_devices": False,
        }

        with patch("custom_components.fing_ha.config_flow.FingAgent") as mock_fing_class:
            mock_fing_instance = MagicMock()
            mock_fing_class.return_value = mock_fing_instance
            mock_fing_instance.get_devices.return_value = {"devices": []}

            result = await config_flow.async_step_user(user_input)

            assert result["type"] == "create_entry"
            assert result["title"] == "Fing HA"
            assert result["data"] == user_input
            mock_fing_class.assert_called_once_with(
                key="test_key", ip="localhost", port=49090
            )
            # The call goes through async_add_executor_job, so we check that instead
            mock_fing_instance.get_devices.assert_called_once()

    @pytest.mark.asyncio
    async def test_step_user_connection_error(self, config_flow):
        """Test user step with connection error."""
        user_input = {
            "host": "localhost",
            "port": 49090,
            "api_key": "test_key",
        }

        with patch("custom_components.fing_ha.config_flow.FingAgent") as mock_fing_class:
            mock_fing_instance = MagicMock()
            mock_fing_class.return_value = mock_fing_instance
            mock_fing_instance.get_devices.side_effect = Exception("Connection failed")

            result = await config_flow.async_step_user(user_input)

            assert result["type"] == "form"
            assert result["errors"]["base"] == "cannot_connect"
            mock_fing_instance.get_devices.assert_called_once()

    @pytest.mark.asyncio
    async def test_step_user_no_input(self, config_flow):
        """Test user step with no input."""
        result = await config_flow.async_step_user(None)

        assert result["type"] == "form"
        assert "data_schema" in result
        assert result["step_id"] == "user"
        assert result["errors"] == {}

    @pytest.mark.asyncio
    async def test_step_user_with_defaults(self, config_flow):
        """Test user step with default values."""
        user_input = {
            "host": "localhost",
            "api_key": "test_key",
        }

        with patch("custom_components.fing_ha.config_flow.FingAgent") as mock_fing_class:
            mock_fing_instance = MagicMock()
            mock_fing_class.return_value = mock_fing_instance
            mock_fing_instance.get_devices.return_value = {"devices": []}

            result = await config_flow.async_step_user(user_input)

            expected_data = {
                "host": "localhost",
                "port": 49090,
                "api_key": "test_key",
                "scan_interval": 30,
                "enable_notifications": False,
                "exclude_unknown_devices": False,
            }
            assert result["data"] == expected_data

    def test_data_schema_validation(self, config_flow):
        """Test data schema validation."""
        schema = config_flow.async_step_user(None)["data_schema"]

        # Valid data
        valid_data = {
            "host": "example.com",
            "port": 443,
            "api_key": "key123",
            "scan_interval": 60,
            "enable_notifications": True,
            "exclude_unknown_devices": True,
        }
        assert schema(valid_data) == valid_data

        # Invalid port
        with pytest.raises(Invalid):
            schema({"host": "example.com", "port": "invalid", "api_key": "key123"})

        # Missing required fields
        with pytest.raises(Invalid):
            schema({"host": "example.com"})
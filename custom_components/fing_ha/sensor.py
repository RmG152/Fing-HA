"""Fing HA sensor platform."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class FingDeviceBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Fing device binary sensor."""

    def __init__(self, coordinator, device_id: str, device_data: dict[str, Any]) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.device_id = device_id
        self._device_data = device_data

        # Use MAC address for unique ID to handle duplicate device names
        mac_address = device_data.get('mac_address', device_id)
        hostname = device_data.get('hostname', device_id)

        # Create unique ID using MAC address
        self._attr_unique_id = f"{DOMAIN}_{mac_address}_online"

        # Create friendly name that includes both hostname and MAC for clarity
        short_mac = mac_address.replace(':', '')[-4:] if ':' in mac_address else mac_address[-4:]
        self._attr_name = f"{hostname} ({short_mac}) Online"

        self._attr_device_class = BinarySensorDeviceClass.PRESENCE
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, mac_address)},
            name=f"{hostname} ({short_mac})",
            manufacturer=device_data.get("vendor", "Unknown"),
            model=device_data.get("device_type", "Unknown"),
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if the device is online."""
        try:
            devices = self.coordinator.data.get("devices")
            if not devices:
                return False

            # Handle DeviceResponse object from Fing API
            if hasattr(devices, '_devices'):
                for device in devices._devices:
                    mac = getattr(device, 'mac_address', getattr(device, 'mac', None))
                    if mac == self.device_id:
                        # Check _device_json first (this is where Fing API stores the data)
                        if hasattr(device, '_device_json') and isinstance(getattr(device, '_device_json'), dict):
                            device_json = getattr(device, '_device_json')
                            if 'state' in device_json:
                                state_value = device_json['state']
                                # 'UP' means online, 'DOWN' means offline
                                return state_value == 'UP'

                        # Fallback to direct attributes if _device_json not available
                        if hasattr(device, 'online'):
                            return bool(getattr(device, 'online'))
                        elif hasattr(device, 'is_online'):
                            return bool(getattr(device, 'is_online'))
                        elif hasattr(device, 'status'):
                            status = getattr(device, 'status')
                            if isinstance(status, str):
                                return status.lower() in ['online', 'true', '1', 'yes', 'up']
                            return bool(status)

                        # Default to True if we can't determine (device exists so it's likely online)
                        _LOGGER.debug("Could not determine online status for device %s, defaulting to online", mac)
                        return True

            # Fallback to dict lookup if devices is a dict
            elif isinstance(devices, dict):
                device_data = devices.get(self.device_id, {})
                online_status = device_data.get("online")
                if online_status is None:
                    return False
                return bool(online_status)

            return False
        except (KeyError, TypeError, AttributeError) as e:
            _LOGGER.debug("Error getting online status for device %s: %s", self.device_id, e)
            return False


class FingDeviceSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Fing device sensor."""

    def __init__(self, coordinator, device_id: str, device_data: dict[str, Any], sensor_type: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.device_id = device_id
        self._device_data = device_data
        self.sensor_type = sensor_type

        # Use MAC address for unique ID to handle duplicate device names
        mac_address = device_data.get('mac_address', device_id)
        hostname = device_data.get('hostname', device_id)

        # Create unique ID using MAC address
        self._attr_unique_id = f"{DOMAIN}_{mac_address}_{sensor_type}"

        # Create friendly name that includes both hostname and MAC for clarity
        short_mac = mac_address.replace(':', '')[-4:] if ':' in mac_address else mac_address[-4:]
        sensor_type_title = sensor_type.title()
        if sensor_type == "ip":
            sensor_type_title = "IP Address"
        elif sensor_type == "first_seen":
            sensor_type_title = "First Seen"
        elif sensor_type == "last_changed":
            sensor_type_title = "Last Changed"
        self._attr_name = f"{hostname} ({short_mac}) {sensor_type_title}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, mac_address)},
            name=f"{hostname} ({short_mac})",
            manufacturer=device_data.get("vendor", "Unknown"),
            model=device_data.get("device_type", "Unknown"),
        )
        # Set attributes based on sensor type
        if sensor_type == "ip":
            # IP addresses don't have a specific device class in this HA version
            pass
        elif sensor_type in ["first_seen", "last_changed"]:
            # Timestamp sensors
            self._attr_device_class = SensorDeviceClass.TIMESTAMP
            self._attr_state_class = None
        # Add more sensor types as needed

    @property
    def native_value(self) -> str | int | None:
        """Return the state of the sensor."""
        try:
            devices = self.coordinator.data.get("devices")
            if not devices:
                return None

            # Handle DeviceResponse object from Fing API
            if hasattr(devices, '_devices'):
                for device in devices._devices:
                    mac = getattr(device, 'mac_address', getattr(device, 'mac', None))
                    if mac == self.device_id:
                        # Check _device_json first for accurate data
                        if hasattr(device, '_device_json') and isinstance(getattr(device, '_device_json'), dict):
                            device_json = getattr(device, '_device_json')

                            if self.sensor_type == "ip":
                                if 'ip' in device_json and device_json['ip']:
                                    # IP is stored as a list, get the first one
                                    ip_list = device_json['ip']
                                    return ip_list[0] if isinstance(ip_list, list) and ip_list else None
                                return None

                            elif self.sensor_type in ["first_seen", "last_changed"]:
                                # Handle timestamp sensors
                                timestamp_value = device_json.get(self.sensor_type)
                                if timestamp_value:
                                    # Parse timestamp if it's a string
                                    if isinstance(timestamp_value, str):
                                        try:
                                            from datetime import datetime
                                            from homeassistant.util import dt as dt_util
                                            # Try common timestamp formats
                                            for fmt in ['%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S']:
                                                try:
                                                    dt = datetime.strptime(timestamp_value, fmt)
                                                    # Make timezone-aware (assume UTC if not specified)
                                                    if dt.tzinfo is None:
                                                        dt = dt_util.utc_from_timestamp(dt.timestamp())
                                                    return dt
                                                except ValueError:
                                                    continue
                                            # If no format matches, return as-is
                                            return timestamp_value
                                        except (ValueError, TypeError):
                                            return None
                                    elif isinstance(timestamp_value, (int, float)):
                                        # Unix timestamp
                                        try:
                                            from homeassistant.util import dt as dt_util
                                            dt = dt_util.utc_from_timestamp(timestamp_value)
                                            return dt
                                        except (ValueError, TypeError, OSError):
                                            return None
                                    else:
                                        return timestamp_value
                                return None

                            else:
                                # Try to get other attributes from _device_json
                                if self.sensor_type in device_json:
                                    return device_json[self.sensor_type]
                                # Fall back to device attributes
                                value = getattr(device, self.sensor_type, None)
                                return value

                        # Fallback to direct device attributes
                        if self.sensor_type == "ip":
                            value = getattr(device, 'ip_address', getattr(device, 'ip', None))
                            return value if value else None
                        elif self.sensor_type in ["first_seen", "last_changed"]:
                            # Handle timestamp sensors from device attributes
                            value = getattr(device, self.sensor_type, None)
                            if value:
                                if isinstance(value, str):
                                    try:
                                        from datetime import datetime
                                        from homeassistant.util import dt as dt_util
                                        # Try common timestamp formats
                                        for fmt in ['%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S']:
                                            try:
                                                dt = datetime.strptime(value, fmt)
                                                # Make timezone-aware (assume UTC if not specified)
                                                if dt.tzinfo is None:
                                                    dt = dt_util.utc_from_timestamp(dt.timestamp())
                                                return dt
                                            except ValueError:
                                                continue
                                        return value
                                    except (ValueError, TypeError):
                                        return None
                                elif isinstance(value, (int, float)):
                                    try:
                                        from homeassistant.util import dt as dt_util
                                        dt = dt_util.utc_from_timestamp(value)
                                        return dt
                                    except (ValueError, TypeError, OSError):
                                        return None
                                else:
                                    return value
                            return None
                        else:
                            # Try to get other attributes
                            value = getattr(device, self.sensor_type, None)
                            return value

            # Fallback to dict lookup if devices is a dict
            elif isinstance(devices, dict):
                device_data = devices.get(self.device_id, {})
                value = device_data.get(self.sensor_type)
                if value is None:
                    return None
                # Handle timestamp sensors
                if self.sensor_type in ["first_seen", "last_changed"]:
                    if value:
                        if isinstance(value, str):
                            try:
                                from datetime import datetime
                                from homeassistant.util import dt as dt_util
                                # Try common timestamp formats
                                for fmt in ['%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S']:
                                    try:
                                        dt = datetime.strptime(value, fmt)
                                        # Make timezone-aware (assume UTC if not specified)
                                        if dt.tzinfo is None:
                                            dt = dt_util.utc_from_timestamp(dt.timestamp())
                                        return dt
                                    except ValueError:
                                        continue
                                return value
                            except (ValueError, TypeError):
                                return None
                        elif isinstance(value, (int, float)):
                            try:
                                from homeassistant.util import dt as dt_util
                                dt = dt_util.utc_from_timestamp(value)
                                return dt
                            except (ValueError, TypeError, OSError):
                                return None
                        else:
                            return value
                    return None
                return value

            return None
        except (KeyError, TypeError, AttributeError) as e:
            _LOGGER.debug("Error getting %s value for device %s: %s", self.sensor_type, self.device_id, e)
            return None


def _create_entities(coordinator, devices):
    """Create entities for large device lists."""
    _LOGGER.debug("Creating entities for devices: %s", devices)
    entities = []

    # Handle None or empty devices
    if devices is None:
        _LOGGER.debug("Devices is None, returning empty entities list")
        return entities

    try:
        if hasattr(devices, '_devices'):
            # Handle DeviceResponse object from fing-agent-api
            devices_list = devices._devices
            _LOGGER.debug("Found DeviceResponse with %d devices", len(devices_list))

            for device in devices_list:
                # Extract basic device info for entity creation
                mac = None
                hostname = f'Device_{mac}'
                vendor = 'Unknown'
                device_type = 'unknown'

                # Get data from _device_json for accuracy
                if hasattr(device, '_device_json') and isinstance(getattr(device, '_device_json'), dict):
                    device_json = getattr(device, '_device_json')
                    mac = device_json.get('mac')
                    hostname = device_json.get('name', f'Device_{mac}')
                    vendor = device_json.get('make', 'Unknown')
                    device_type = device_json.get('type', 'unknown')

                # Fallback to device attributes if _device_json not available
                if not mac:
                    mac = getattr(device, 'mac_address', getattr(device, 'mac', None))
                if not mac:
                    continue

                if hostname == f'Device_{mac}':  # Still default
                    hostname = getattr(device, 'hostname', getattr(device, 'name', f'Device_{mac}'))
                if vendor == 'Unknown':
                    vendor = getattr(device, 'vendor', 'Unknown')
                if device_type == 'unknown':
                    device_type = getattr(device, 'device_type', 'unknown')

                # Create device_data dict for entity initialization
                device_data = {
                    'mac_address': mac,
                    'hostname': hostname,
                    'vendor': vendor,
                    'device_type': device_type,
                }

                _LOGGER.debug("Creating entities for device %s: %s", mac, device_data)
                entities.append(FingDeviceBinarySensor(coordinator, mac, device_data))
                # Add multiple sensors per device
                for sensor_type in ["ip", "first_seen", "last_changed"]:
                    entities.append(FingDeviceSensor(coordinator, mac, device_data, sensor_type))

        elif hasattr(devices, 'items'):
            # Handle dict-like devices
            devices_dict = dict(devices.items())
            _LOGGER.debug("Converted devices using items(): %s", devices_dict)

            for device_id, device_data in devices_dict.items():
                _LOGGER.debug("Creating entities for device %s: %s", device_id, device_data)
                entities.append(FingDeviceBinarySensor(coordinator, device_id, device_data))
                # Add multiple sensors per device
                for sensor_type in ["ip", "first_seen", "last_changed"]:
                    entities.append(FingDeviceSensor(coordinator, device_id, device_data, sensor_type))

        else:
            _LOGGER.debug("No supported device format found, creating empty entities list")

    except Exception as e:
        _LOGGER.debug("Error creating entities: %s", e)

    _LOGGER.debug("Entity creation complete, created %d entities", len(entities))
    return entities


# New helper: run filtering + creation in a thread to avoid blocking the event loop
def _prepare_entities_sync(coordinator, devices, exclude_unknown_devices, previous_devices):
    """Prepare and create entities off the event loop."""
    try:
        # Ensure devices is a safe value for processing
        if devices is None:
            devices = {}

        # Perform the same filtering logic synchronously (safe to run in executor)
        if exclude_unknown_devices:
            try:
                if hasattr(devices, '_devices'):
                    filtered_devices = []
                    for device in devices._devices:
                        device_id = getattr(device, 'mac_address', getattr(device, 'mac', None))
                        if device_id and device_id in previous_devices:
                            filtered_devices.append(device)
                    class FilteredDeviceResponse:
                        def __init__(self, devices_list, orig):
                            self._devices = devices_list
                            self._network_id = getattr(orig, '_network_id', None)
                    devices = FilteredDeviceResponse(filtered_devices, devices)
                elif hasattr(devices, 'items'):
                    devices = {k: v for k, v in devices.items() if k in previous_devices}
                elif hasattr(devices, '__iter__') and not isinstance(devices, (str, bytes)):
                    devices = [item for i, item in enumerate(devices) if str(i) in previous_devices]
                else:
                    devices = {}
            except Exception as e:
                _LOGGER.debug("Error filtering devices in executor: %s", e)
                devices = {}

        # Create entities (this calls the existing _create_entities helper)
        entities = _create_entities(coordinator, devices)
        return entities
    except Exception as e:
        _LOGGER.debug("Error preparing entities in executor: %s", e)
        return []

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fing HA sensor platform."""
    _LOGGER.debug("Setting up Fing HA sensor platform")
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    # Keep the event-loop work minimal: only access small pieces of data here
    _LOGGER.debug("Coordinator data (before create): %s", coordinator.data)

    devices = {} if coordinator.data is None else coordinator.data.get("devices", {})

    _LOGGER.debug("Devices from coordinator: %s", devices)
    _LOGGER.debug("Devices type: %s", type(devices))

    # Prepare entities entirely in executor (includes filtering)
    exclude = entry.data.get("exclude_unknown_devices", False)
    previous = hass.data[DOMAIN][entry.entry_id].get("previous_devices", {})

    # log start time for measurement
    import time
    start = time.perf_counter()
    entities = await hass.async_add_executor_job(
        _prepare_entities_sync, coordinator, devices, exclude, previous
    )
    duration = time.perf_counter() - start
    _LOGGER.debug("Entity preparation took %.3f seconds", duration)

    # Register entities asynchronously so async_setup_entry returns promptly
    async def _async_register_entities():
        try:
            async_add_entities(entities)
            _LOGGER.info("Created %d sensor entities for Fing HA", len(entities))
        except Exception as e:
            _LOGGER.exception("Error registering Fing HA entities: %s", e)

    # Schedule registration and return immediately (avoid awaiting heavy work)
    hass.async_create_task(_async_register_entities())

    async def async_update(self) -> None:
        """Update sensor state from Fing."""
        try:
            _LOGGER.debug("Updating Fing sensor data")
            # Use the async API which already runs blocking work in the executor
            devices = await self._api.async_get_devices()

            # Process devices with the entity helper (avoids NameError)
            self._state = self._process_devices(devices)

        except Exception as err:
             _LOGGER.error("Error updating Fing sensor: %s", err)

    def _process_devices(self, devices):
        """Convert Fing API devices payload into a sensor state.

        Default: if `devices` is an iterable return its length; if it is a dict and contains
        'devices' return the length of that list; otherwise return the string representation.
        Adjust this function according to the exact payload structure.
        """
        try:
            if isinstance(devices, dict):
                if "devices" in devices and hasattr(devices["devices"], "__len__"):
                    return len(devices["devices"])
                # si el dict ya es el estado esperado, devolverlo tal cual
                return devices
            if hasattr(devices, "__len__") and not isinstance(devices, (str, bytes)):
                return len(devices)
        except Exception:
            _LOGGER.debug("Fing sensor: _process_devices fallback used", exc_info=True)
        return str(devices)
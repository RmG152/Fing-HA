[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/H2H81ICGVI)

# Fing HA Integration

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/docs/setup/download#hacs)

Seamlessly integrate Fing's powerful network scanning capabilities into Home Assistant. Automatically discover and track devices on your local network with real-time insights and comprehensive network monitoring.

## Features

- **Automatic Device Discovery**: Real-time detection of devices joining/leaving your network
- **Device Tracking**: Monitor device online/offline status
- **Network Statistics**: Get detailed network performance metrics
- **Event Monitoring**: Track network events and device connections
- **Home Assistant Integration**: Native sensors and entities for automation

## Installation

### Option 1: HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Go to "Integrations" → "⋮" (Menu) → "Custom repositories"
3. Add https://github.com/RmG152/Fing-HA as the repository URL and select "Integration" as category
4. Search for "Fing HA" and install it
5. Restart Home Assistant

### Option 2: Manual Installation

1. Download the `custom_components/fing_ha/` folder from this repository
2. Copy it to your Home Assistant's `custom_components/` directory
3. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "Fing HA" and select it
3. Enter your Fing API configuration:
   - **Host**: Your Fing server hostname/IP
   - **Port**: API port (default: 49090)
   - **API Key**: Your Fing API key
   - **Scan Interval**: How often to scan for devices (default: 30 seconds)
   - **Enable Notifications**: Send notifications for new devices
   - **Exclude Unknown Devices**: Only show previously known devices

![Configuration Screenshot](screenshots/configuration.png)

## Usage

Once configured, the integration will automatically:

- Create binary sensors for each device showing online/offline status
- Create sensors for device IP addresses, first seen timestamps, and last changed timestamps
- Update entities in real-time based on the scan interval

### Available Entities

- **Binary Sensor**: `{device_name} Online` - Shows if device is connected
- **Sensor**: `{device_name} IP` - Current IP address
- **Sensor**: `{device_name} First Seen` - Timestamp when device was first detected
- **Sensor**: `{device_name} Last Changed` - Timestamp when device status last changed

### Automations

Create automations based on device events:

```yaml
# Example: Notify when specific device comes online
trigger:
  platform: state
  entity_id: binary_sensor.my_phone_online
  to: 'on'
action:
  service: notify.mobile_app
  data:
    message: "Phone is now online"
```

## Troubleshooting

### Common Issues

**"Cannot connect to Fing API"**
- Verify your host and port are correct
- Check if the Fing service is running
- Ensure your API key is valid

**"No devices detected"**
- Confirm network scanning permissions
- Check if devices are on the same network segment
- Verify the scan interval setting

**"Integration not loading"**
- Check Home Assistant logs for error messages
- Ensure all dependencies are installed
- Restart Home Assistant after installation

### Debug Logging

Enable debug logging for the integration:

```yaml
logger:
  logs:
    custom_components.fing_ha: debug
```

### Testing the API Connection

You can test the integration using the included test connection feature during setup.

## API Reference

The integration provides the following API methods:

- `async_get_devices()`: Get devices from Fing API
- `async_test_connection()`: Test API connectivity

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:

- Open an issue on GitHub
- Check the Home Assistant community forums
- Review the troubleshooting section above

---

*Note: This integration requires a working Fing installation with API access enabled.*

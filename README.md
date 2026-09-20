**English** | [Русский](README.ru.md)

# BLE-C600 for Home Assistant

C600 Bluetooth sensor integration based on [Dutch-Al/BLE-C600](https://github.com/Dutch-Al/BLE-C600), with fixes for BLE reads and retention of the last readings.

Supports pH, electrical conductivity, TDS, ORP, free chlorine, temperature, calculated salt content and battery level. Polling interval: 60 seconds.

## Installation

### Automatically

> [!TIP]
> Recommended installation method. HACS must be installed in Home Assistant.

[![Open the repository in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=OlegKocha&repository=BLE-C600&category=integration)

1. Click the button above and open the repository in HACS.
2. If the repository has not been added yet, open “Custom repositories” in HACS and add `https://github.com/OlegKocha/BLE-C600` with the “Integration” category.
3. Find `ble-c600` in HACS and download the integration.
4. Restart Home Assistant.

### Manually

In the Home Assistant terminal, clone the repository into a temporary directory and copy the integration to `/config/custom_components/`:

```bash
c600_tmp=$(mktemp -d)
git clone https://github.com/OlegKocha/BLE-C600.git "$c600_tmp/BLE-C600"
mkdir -p /config/custom_components
cp -R "$c600_tmp/BLE-C600/custom_components/ble_c600" /config/custom_components/
```

Restart Home Assistant. If your installation uses a configuration directory other than `/config`, replace the path in the commands.

### Configuration

1. Open “Settings → Devices & services → Add integration”.
2. Find `ble_c600` and follow the setup wizard.
3. Switch on C600 and wait for the first readings.

## Operation

Switch on C600 and wait for the first read. When the connection is lost, the last values are retained; the `data_stale` attribute indicates that they are stale, and `last_successful_read` shows the time of the last successful read. After restarting HA or reloading the integration, a new read is required: the cache is stored in memory.

## License

[MIT](LICENSE). Original project: [Dutch-Al/BLE-C600](https://github.com/Dutch-Al/BLE-C600), original code author: jdeath.

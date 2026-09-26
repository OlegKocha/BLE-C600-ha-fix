**English** | [Русский](README.ru.md)

# BLE-C600 for Home Assistant

C600 Bluetooth sensor integration based on [Dutch-Al/BLE-C600](https://github.com/Dutch-Al/BLE-C600), with fixes for BLE reads and retention of the last readings.

Supports pH, electrical conductivity, TDS, ORP, free chlorine, temperature, calculated salt content and battery level. Polling interval: 60 seconds.

## Installation

### Automatically

> [!TIP]
> Recommended installation method. HACS must be installed in Home Assistant.

[![Open the repository in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=OlegKocha&repository=BLE-C600-ha-fix&category=integration)

1. Click the button above and open the repository in HACS.
2. If the repository has not been added yet, open “Custom repositories” in HACS and add `https://github.com/OlegKocha/BLE-C600-ha-fix` with the “Integration” category.
3. Find `ble-c600` in HACS and download the integration.
4. Restart Home Assistant.

### Manually

In the Home Assistant terminal, clone the repository into a temporary directory and copy the integration to `/config/custom_components/`:

```bash
c600_tmp=$(mktemp -d)
git clone https://github.com/OlegKocha/BLE-C600-ha-fix.git "$c600_tmp/BLE-C600-ha-fix"
mkdir -p /config/custom_components
cp -R "$c600_tmp/BLE-C600-ha-fix/custom_components/ble_c600" /config/custom_components/
```

Restart Home Assistant. If your installation uses a configuration directory other than `/config`, replace the path in the commands.

### Configuration

1. Open “Settings → Devices & services → Add integration”.
2. Find `ble_c600` and follow the setup wizard.
3. Switch on C600 and wait for the first readings.

## Operation

The integration loads all eight sensors even if C600 is switched off when Home Assistant starts. It keeps polling the saved Bluetooth address every 60 seconds and resumes updates when the device becomes available.

After a successful read, values are retained during BLE outages and restored after a Home Assistant restart or integration reload. Restored readings are marked `data_stale: true`; `last_successful_read` keeps the original read time until fresh data arrives. Values are saved using Home Assistant's sensor state restoration mechanism, in their native units.

If no saved reading exists for a sensor, it remains unavailable until C600 supplies one; the integration itself still loads. Versions 1.0 and 1.0.1 did not save values for restart restoration, so after upgrading to 1.0.2 you need one successful read before values can be restored on future restarts.

When updating through HACS, use [OlegKocha/BLE-C600-ha-fix](https://github.com/OlegKocha/BLE-C600-ha-fix). Updating the original repository can overwrite these fixes. Keep the existing device configuration: removing and adding the device again is not required.

## License

[MIT](LICENSE). Original project: [Dutch-Al/BLE-C600](https://github.com/Dutch-Al/BLE-C600), original code author: jdeath.

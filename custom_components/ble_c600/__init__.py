"""The C600 BLE integration."""
from __future__ import annotations

from datetime import timedelta
import logging

from .BLE_C600 import C600BluetoothDeviceData, C600Device

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up C600 BLE device from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    address = entry.unique_id

    assert address is not None

    async def _async_update_method():
        """Get data from C600 BLE."""
        ble_device = bluetooth.async_ble_device_from_address(hass, address)
        if ble_device is None:
            # A powered-off device is expected, including during HA startup.
            # Empty readings mark the entity caches stale without blocking setup.
            _LOGGER.debug("C600 %s is offline; waiting for it to return", address)
            return C600Device(name=address, address=address)
        c600 = C600BluetoothDeviceData(_LOGGER)

        try:
            data = await c600.update_device(ble_device)
        except Exception as err:
            raise UpdateFailed(f"Unable to fetch data: {err}") from err

        return data
        
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        config_entry=entry,
        update_method=_async_update_method,
        update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
    )

    # Create the entities even when the first BLE read fails. Their restored
    # values remain visible, and coordinator listeners keep scheduling polls.
    await coordinator.async_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

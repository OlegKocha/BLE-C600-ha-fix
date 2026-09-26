"""C600 sensors: retain readings across BLE outages and HA restarts."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from math import isfinite

from .BLE_C600 import C600Device

from homeassistant import config_entries
from homeassistant.components.sensor import (
    SensorDeviceClass,
    RestoreSensor,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    UnitOfTemperature,
    UnitOfElectricPotential,
    UnitOfConductivity,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SENSORS_MAPPING_TEMPLATE: dict[str, SensorEntityDescription] = {
    "EC": SensorEntityDescription(
        key="EC",
        name="Electrical Conductivity",
        native_unit_of_measurement=UnitOfConductivity.MICROSIEMENS_PER_CM,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash-triangle-outline",
    ),
    "salt": SensorEntityDescription(
        key="salt",
        name="Salt",
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:shaker-outline",
    ),
    "ORP": SensorEntityDescription(
        key="ORP",
        name="Oxidation-Reduction Potential",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.VOLTAGE,
        icon="mdi:alpha-v-circle",
    ),
    "TDS": SensorEntityDescription(
        key="TDS",
        name="Total Dissolved Solids",
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:dots-grid",
    ),
    "pH": SensorEntityDescription(
        key="pH",
        name="pH",
        device_class=SensorDeviceClass.PH,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:ph",
    ),
    "battery": SensorEntityDescription(
        key="battery",
        name="Battery",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
    ),
    "cloro": SensorEntityDescription(
        key="cloro",
        name="Free Chlorine",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        icon="mdi:chemical-weapon",
    ),
    "temperature": SensorEntityDescription(
        key="temperature",
        name="Temperature",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        icon="mdi:pool-thermometer",
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the C600 BLE sensors."""
    coordinator: DataUpdateCoordinator[C600Device] = hass.data[DOMAIN][entry.entry_id]
    address = entry.unique_id
    assert address is not None
    # Preserve the identity used by successful reads in previous versions.
    # All eight entities must exist even if the device is offline at startup.
    device = C600Device(name=address, address=address)
    async_add_entities(
        C600Sensor(coordinator, device, description)
        for description in SENSORS_MAPPING_TEMPLATE.values()
    )


class C600Sensor(CoordinatorEntity[DataUpdateCoordinator[C600Device]], RestoreSensor):
    """C600 BLE sensors for the device."""

    #_attr_state_class = SensorStateClass.MEASUREMENT
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        C600_device: C600Device,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Populate the C600 entity with relevant data."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._last_value: StateType = None
        self._last_successful_read: str | None = None
        self._data_stale = True
        self._cache_successful_reading()

        name = f"{C600_device.name} {C600_device.identifier}"

        self._attr_unique_id = f"{name}_{entity_description.key}"

        self._id = C600_device.address
        self._attr_device_info = DeviceInfo(
            connections={
                (
                    CONNECTION_BLUETOOTH,
                    C600_device.address,
                )
            },
            name=name,
            manufacturer="C600",
            model="C600",
            hw_version=C600_device.hw_version,
            sw_version=C600_device.sw_version,
        )

    async def async_added_to_hass(self) -> None:
        """Restore native readings and their timestamps, without making them fresh."""
        await super().async_added_to_hass()
        if self._last_value is not None:
            return

        restored = await self.async_get_last_sensor_data()
        last_state = await self.async_get_last_state()
        # A BLE update may arrive while restore data is being loaded.
        if self._last_value is not None or restored is None:
            return
        value = restored.native_value
        if (
            restored.native_unit_of_measurement != self.native_unit_of_measurement
            or isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not isfinite(value)
        ):
            return

        # Never restore a displayed state as a native value (e.g. mV as V).
        self._last_value = value
        if last_state is not None:
            timestamp = last_state.attributes.get("last_successful_read")
            if isinstance(timestamp, str):
                self._last_successful_read = timestamp
        self._data_stale = True

    @callback
    def _cache_successful_reading(self) -> None:
        """Keep the last received value when a poll fails or omits this field."""
        self._data_stale = True
        if not self.coordinator.last_update_success or self.coordinator.data is None:
            return
        value = self.coordinator.data.sensors.get(self.entity_description.key)
        if value is None:
            return
        self._last_value = value
        self._last_successful_read = datetime.now(timezone.utc).isoformat()
        self._data_stale = False

    @callback
    def _handle_coordinator_update(self) -> None:
        """Publish new readings or mark the retained readings as stale."""
        self._cache_successful_reading()
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Stay available with a live or restored reading, even when offline."""
        return self._last_value is not None

    @property
    def native_value(self) -> StateType:
        """Return the latest successfully received value, including zero."""
        return self._last_value

    @property
    def extra_state_attributes(self) -> dict[str, str | bool | None]:
        """Expose freshness separately from the retained measurement."""
        return {
            "data_stale": self._data_stale,
            "last_successful_read": self._last_successful_read,
        }

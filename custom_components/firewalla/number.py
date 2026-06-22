"""Number platform for Firewalla MQTT Bridge."""

from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number entities from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    prefix = entry.data.get("mqtt_prefix", "firewalla")

    entities: list[NumberEntity] = []

    # Collect interval number entity
    entities.append(
        FirewallaCollectIntervalNumber(
            coordinator=coordinator,
            prefix=prefix,
        )
    )

    async_add_entities(entities)


class FirewallaCollectIntervalNumber(CoordinatorEntity, NumberEntity):
    """Representation of a collect interval number entity."""

    _attr_has_entity_name = True
    _attr_native_min_value = 30
    _attr_native_max_value = 3600
    _attr_native_step = 30
    _attr_native_unit_of_measurement = "s"
    _attr_entity_category = "config"

    def __init__(
        self,
        coordinator=None,
        prefix: str = "firewalla",
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._attr_name = "Collect Interval"
        self._attr_unique_id = "firewalla_collect_interval"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "firewalla_box")},
            name="Firewalla",
            manufacturer=MANUFACTURER,
            model="Firewalla Smart Security",
        )
        self._attr_native_value = 60  # default

    @property
    def native_value(self) -> int | None:
        """Return the current collect interval."""
        # This would be read from config or a dedicated MQTT topic
        # For now, return the default
        return 60

    async def async_set_native_value(self, value: float) -> None:
        """Set the collect interval."""
        _LOGGER.info("Collect interval change requested: %d", int(value))
        # Note: This would require writing to the bridge config
        # For now, log the request

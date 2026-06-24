"""Text platform for Firewalla MQTT Bridge."""

from __future__ import annotations

import logging

from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, TOPIC_HOST

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up text entities from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    coordinator = data["coordinator"]
    prefix = entry.data.get("mqtt_prefix", "firewalla")

    entities: list[TextEntity] = []

    # Per-device name text entities
    hosts_data = client.received_messages.get(f"{prefix}/network/hosts", {})
    online_devices = hosts_data.get("online", [])
    for device in online_devices:
        mac = device.get("mac", "")
        if mac:
            mac_underscore = mac.replace(":", "_")
            entities.append(
                FirewallaDeviceTextEntity(
                    device_name=device.get("name", "Unknown"),
                    mac=mac,
                    mac_underscore=mac_underscore,
                    coordinator=coordinator,
                    client=client,
                    prefix=prefix,
                )
            )

    async_add_entities(entities)


class FirewallaDeviceTextEntity(CoordinatorEntity, TextEntity):
    """Representation of a per-device text entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        device_name: str,
        mac: str,
        mac_underscore: str,
        coordinator=None,
        client=None,
        prefix: str = "firewalla",
    ) -> None:
        """Initialize the text entity."""
        super().__init__(coordinator)
        self._device_name = device_name
        self._mac = mac
        self._mac_underscore = mac_underscore
        self._client = client
        self._prefix = prefix
        self._attr_name = f"{device_name} Name"
        self._attr_unique_id = f"firewalla_device_{mac_underscore}_name"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, mac_underscore)},
            name=device_name,
            via_device=(DOMAIN, "firewalla_box"),
        )

    @property
    def native_value(self) -> str | None:
        """Return the value of the text entity."""
        topic = f"{self._prefix}/{TOPIC_HOST}/{self._mac_underscore}"
        payload = self.coordinator.data.get(topic)
        if payload:
            return payload.get("name")
        return self._device_name

    async def async_set_value(self, value: str) -> None:
        """Set the value."""
        # Note: Firewalla device names are set via the Firewalla API, not MQTT
        # This is a placeholder for future implementation
        _LOGGER.info("Device name change requested for %s: %s", self._mac, value)

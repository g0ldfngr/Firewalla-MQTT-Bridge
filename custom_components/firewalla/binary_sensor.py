"""Binary sensor platform for Firewalla MQTT Bridge."""

from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MANUFACTURER,
    BINARY_SENSOR_ENTITIES,
    TOPIC_BOX_INFO,
)
from .mqtt_client import FirewallaMQTTClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensor entities from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    client: FirewallaMQTTClient = data["client"]
    coordinator = data["coordinator"]
    prefix = entry.data.get("mqtt_prefix", "firewalla")

    entities: list[BinarySensorEntity] = []

    # Main Firewalla box binary sensors
    for entity_conf in BINARY_SENSOR_ENTITIES:
        entities.append(
            FirewallaBinarySensorEntity(
                name=entity_conf["name"],
                topic=f"{prefix}/{entity_conf['topic']}",
                value_template=entity_conf.get("value_template"),
                device_class=entity_conf.get("device_class"),
                entity_category=entity_conf.get("entity_category"),
                coordinator=coordinator,
                key=entity_conf["key"],
            )
        )

    # Per-device online binary sensors
    hosts_data = client.received_messages.get(f"{prefix}/network/hosts", {})
    online_devices = hosts_data.get("online", [])
    for device in online_devices:
        mac = device.get("mac", "")
        if mac:
            mac_underscore = mac.replace(":", "_")
            entities.append(
                FirewallaDeviceBinarySensorEntity(
                    device_name=device.get("name", "Unknown"),
                    mac=mac,
                    mac_underscore=mac_underscore,
                    coordinator=coordinator,
                    client=client,
                    prefix=prefix,
                )
            )

    async_add_entities(entities)


class FirewallaBinarySensorEntity(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Firewalla binary sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        name: str,
        topic: str,
        value_template: str | None,
        device_class: str | None = None,
        entity_category: str | None = None,
        coordinator=None,
        key: str = "",
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = f"firewalla_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "firewalla_box")},
            name="Firewalla",
            manufacturer=MANUFACTURER,
            model="Firewalla Smart Security",
        )
        self._topic = topic
        self._value_template = value_template
        self._attr_device_class = device_class
        if entity_category is not None:
            try:
                self._attr_entity_category = EntityCategory(entity_category)
            except ValueError:
                self._attr_entity_category = None
        else:
            self._attr_entity_category = None

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        payload = self.coordinator.data.get(self._topic)
        if payload is None:
            return None

        if self._value_template:
            from jinja2 import Template
            try:
                tmpl = Template(self._value_template)
                result = tmpl.render(value_json=payload)
                return result.lower() in ("true", "1", "yes")
            except Exception:
                return None

        return bool(payload)


class FirewallaDeviceBinarySensorEntity(CoordinatorEntity, BinarySensorEntity):
    """Representation of a per-device online binary sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        device_name: str,
        mac: str,
        mac_underscore: str,
        coordinator=None,
        client: FirewallaMQTTClient | None = None,
        prefix: str = "firewalla",
    ) -> None:
        """Initialize the device binary sensor."""
        super().__init__(coordinator)
        self._device_name = device_name
        self._mac = mac
        self._mac_underscore = mac_underscore
        self._client = client
        self._prefix = prefix
        self._attr_name = f"{device_name} Online"
        self._attr_unique_id = f"firewalla_device_{mac_underscore}_online"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, mac_underscore)},
            name=device_name,
            via_device=(DOMAIN, "firewalla_box"),
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if the device is online."""
        topic = f"{self._prefix}/network/host/{self._mac_underscore}"
        payload = self.coordinator.data.get(topic)
        if payload:
            return bool(payload.get("online"))
        return None

"""Sensor platform for Firewalla MQTT Bridge."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MANUFACTURER,
    NAME,
    SENSOR_ENTITIES,
    TOPIC_HOST,
    TOPIC_HOSTS,
)
from .mqtt_client import FirewallaMQTTClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    client: FirewallaMQTTClient = data["client"]
    coordinator = data["coordinator"]
    prefix = entry.data.get("mqtt_prefix", "firewalla")

    entities: list[SensorEntity] = []

    # Main Firewalla box sensors
    for entity_conf in SENSOR_ENTITIES:
        entities.append(
            FirewallaSensorEntity(
                name=entity_conf["name"],
                topic=f"{prefix}/{entity_conf['topic']}",
                value_template=entity_conf.get("value_template"),
                unit_of_measurement=entity_conf.get("unit_of_measurement"),
                device_class=entity_conf.get("device_class"),
                state_class=entity_conf.get("state_class"),
                entity_category=entity_conf.get("entity_category"),
                coordinator=coordinator,
                key=entity_conf["key"],
            )
        )

    # Per-device sensors from hosts data
    hosts_data = client.received_messages.get(f"{prefix}/{TOPIC_HOSTS}", {})
    online_devices = hosts_data.get("online", [])
    for device in online_devices:
        mac = device.get("mac", "")
        if mac:
            mac_underscore = mac.replace(":", "_")
            entities.append(
                FirewallaDeviceSensorEntity(
                    device_name=device.get("name", "Unknown"),
                    mac=mac,
                    mac_underscore=mac_underscore,
                    coordinator=coordinator,
                    client=client,
                    prefix=prefix,
                )
            )

    async_add_entities(entities)


class FirewallaSensorEntity(CoordinatorEntity, SensorEntity):
    """Representation of a Firewalla sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        name: str,
        topic: str,
        value_template: str | None,
        unit_of_measurement: str | None = None,
        device_class: str | None = None,
        state_class: str | None = None,
        entity_category: str | None = None,
        coordinator=None,
        key: str = "",
    ) -> None:
        """Initialize the sensor."""
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
        self._attr_native_unit_of_measurement = unit_of_measurement
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        if entity_category is not None:
            try:
                self._attr_entity_category = EntityCategory(entity_category)
            except ValueError:
                self._attr_entity_category = None
        else:
            self._attr_entity_category = None
        self._attr_extra_state_attributes = {}

    @property
    def native_value(self):
        """Return the state."""
        payload = self.coordinator.data.get(self._topic)
        if payload is None:
            return None

        if self._value_template:
            from jinja2 import Template
            try:
                tmpl = Template(self._value_template)
                return tmpl.render(value_json=payload)
            except Exception:
                return None

        return payload


class FirewallaDeviceSensorEntity(CoordinatorEntity, SensorEntity):
    """Representation of a per-device Firewalla sensor."""

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
        """Initialize the device sensor."""
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
        self._attr_extra_state_attributes = {
            "mac": mac,
            "ip": None,
        }

    @property
    def native_value(self):
        """Return the state (online/offline)."""
        topic = f"{self._prefix}/{TOPIC_HOST}/{self._mac_underscore}"
        payload = self.coordinator.data.get(topic)
        if payload:
            self._attr_extra_state_attributes["ip"] = payload.get("ip")
            return "online" if payload.get("online") else "offline"
        return None

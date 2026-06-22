"""Firewalla MQTT Bridge — HACS Custom Integration.

Subscribes to Firewalla MQTT topics and creates native Home Assistant entities
(sensors, binary sensors, text, number) via MQTT discovery.

Requires the Firewalla-to-MQTT bridge (Supervisor add-on or standalone) to be
running and publishing to the configured MQTT broker.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_FIREWALLA_IP,
    CONF_MQTT_BROKER,
    CONF_MQTT_PASSWORD,
    CONF_MQTT_PORT,
    CONF_MQTT_PREFIX,
    CONF_MQTT_USERNAME,
    DEFAULT_MQTT_PREFIX,
    DOMAIN,
    MANUFACTURER,
    NAME,
)
from .mqtt_client import FirewallaMQTTClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "text", "number", "device_tracker"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Firewalla from a config entry."""
    broker = entry.data.get(CONF_MQTT_BROKER, "10.100.255.22")
    port = entry.data.get(CONF_MQTT_PORT, 1833)
    prefix = entry.data.get(CONF_MQTT_PREFIX, DEFAULT_MQTT_PREFIX)
    username = entry.data.get(CONF_MQTT_USERNAME, "")
    password = entry.data.get(CONF_MQTT_PASSWORD, "")
    fw_ip = entry.data.get(CONF_FIREWALLA_IP, "10.100.255.1")

    client = FirewallaMQTTClient(
        hass=hass,
        broker=broker,
        port=port,
        topic_prefix=prefix,
        username=username,
        password=password,
        firewalla_ip=fw_ip,
    )

    try:
        await client.connect()
    except Exception as err:
        _LOGGER.error("Failed to connect to MQTT broker: %s", err)
        raise ConfigEntryNotReady(f"MQTT connection failed: {err}") from err

    coordinator = FirewallaCoordinator(hass, client, prefix)
    await coordinator.async_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    from .services import async_setup_services
    await async_setup_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        client: FirewallaMQTTClient = hass.data[DOMAIN][entry.entry_id]["client"]
        await client.disconnect()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class FirewallaCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Collect latest Firewalla data from MQTT."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: FirewallaMQTTClient,
        prefix: str,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=NAME,
            update_interval=timedelta(seconds=60),
        )
        self._client = client
        self._prefix = prefix

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch latest data from MQTT."""
        data = {}
        for topic, payload in self._client.received_messages.items():
            if topic.startswith(self._prefix + "/"):
                data[topic] = payload
        if not data:
            raise UpdateFailed("No Firewalla data received from MQTT")
        return data

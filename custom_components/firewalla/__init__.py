"""Firewalla MQTT Bridge — HACS Custom Integration.

Subscribes to Firewalla MQTT topics and creates native Home Assistant entities
(sensors, binary sensors, text, number) via HA's built-in MQTT integration.

Requires the Firewalla-to-MQTT bridge (Supervisor add-on or standalone) to be
running and publishing to the configured MQTT broker.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_FIREWALLA_IP,
    CONF_MQTT_PREFIX,
    DEFAULT_MQTT_PREFIX,
    DOMAIN,
    NAME,
)
from .mqtt_client import FirewallaMQTTClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "text", "number", "device_tracker"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Firewalla from a config entry."""
    prefix = entry.data.get(CONF_MQTT_PREFIX, DEFAULT_MQTT_PREFIX)
    fw_ip = entry.data.get(CONF_FIREWALLA_IP, "192.168.0.1")

    client = FirewallaMQTTClient(
        hass=hass,
        topic_prefix=prefix,
        firewalla_ip=fw_ip,
    )

    coordinator = FirewallaCoordinator(hass, client, prefix)
    client.set_coordinator(coordinator)

    await client.connect()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

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
    """Coordinator that holds the latest Firewalla data from MQTT.

    Data is primarily updated via push (async_set_updated_data) from the MQTT
    client.  The timed refresh serves as a fallback heartbeat.
    """

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
        """Return the latest snapshot of all received MQTT messages."""
        return dict(self._client.received_messages)

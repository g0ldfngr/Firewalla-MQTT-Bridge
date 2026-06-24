"""MQTT client for Firewalla data — uses HA's built-in MQTT integration."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components import mqtt
from homeassistant.core import HomeAssistant, callback

from .const import (
    TOPIC_ALARMS,
    TOPIC_ALARMS_SUMMARY,
    TOPIC_BOX_FEATURES,
    TOPIC_BOX_INFO,
    TOPIC_HOST,
    TOPIC_HOSTS,
    TOPIC_HOSTS_SUMMARY,
    TOPIC_LIVE_STATS,
    TOPIC_SPEEDTEST,
    TOPIC_STATUS,
    TOPIC_USAGE,
)

if TYPE_CHECKING:
    from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class FirewallaMQTTClient:
    """Subscribes to Firewalla MQTT topics via HA's built-in MQTT integration."""

    def __init__(
        self,
        hass: HomeAssistant,
        topic_prefix: str,
        firewalla_ip: str = "",
    ) -> None:
        self._hass = hass
        self._prefix = topic_prefix
        self._firewalla_ip = firewalla_ip
        self.received_messages: dict[str, Any] = {}
        self._unsubscribe_callbacks: list = []
        self._coordinator: DataUpdateCoordinator | None = None

    def set_coordinator(self, coordinator: DataUpdateCoordinator) -> None:
        self._coordinator = coordinator

    async def connect(self) -> None:
        """Subscribe to all Firewalla MQTT topics."""
        prefix = self._prefix
        topics = [
            f"{prefix}/{TOPIC_STATUS}",
            f"{prefix}/{TOPIC_LIVE_STATS}",
            f"{prefix}/{TOPIC_HOSTS_SUMMARY}",
            f"{prefix}/{TOPIC_HOSTS}",
            f"{prefix}/{TOPIC_HOST}/#",
            f"{prefix}/{TOPIC_ALARMS_SUMMARY}",
            f"{prefix}/{TOPIC_ALARMS}",
            f"{prefix}/{TOPIC_USAGE}",
            f"{prefix}/{TOPIC_SPEEDTEST}",
            f"{prefix}/{TOPIC_BOX_INFO}",
            f"{prefix}/{TOPIC_BOX_FEATURES}",
        ]
        for topic in topics:
            unsub = await mqtt.async_subscribe(self._hass, topic, self._on_message, qos=1)
            self._unsubscribe_callbacks.append(unsub)
            _LOGGER.debug("Subscribed to %s", topic)

    async def disconnect(self) -> None:
        """Unsubscribe from all topics."""
        for unsub in self._unsubscribe_callbacks:
            unsub()
        self._unsubscribe_callbacks.clear()

    @callback
    def _on_message(self, msg: mqtt.ReceiveMessage) -> None:
        """Handle an incoming MQTT message and push data to the coordinator."""
        try:
            payload = json.loads(msg.payload)
            self.received_messages[msg.topic] = payload
            _LOGGER.debug("Received %s", msg.topic)
            if self._coordinator is not None:
                self._coordinator.async_set_updated_data(dict(self.received_messages))
        except (json.JSONDecodeError, UnicodeDecodeError):
            _LOGGER.warning("Invalid JSON on topic %s", msg.topic)

"""MQTT client for Firewalla data."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from homeassistant.core import HomeAssistant
import paho.mqtt.client as mqtt

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

_LOGGER = logging.getLogger(__name__)


class FirewallaMQTTClient:
    """MQTT client that subscribes to Firewalla topics."""

    def __init__(
        self,
        hass: HomeAssistant,
        broker: str,
        port: int,
        topic_prefix: str,
        username: str = "",
        password: str = "",
        firewalla_ip: str = "",
    ) -> None:
        self._hass = hass
        self._broker = broker
        self._port = port
        self._prefix = topic_prefix
        self._username = username
        self._password = password
        self._firewalla_ip = firewalla_ip
        self._client = mqtt.Client()
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect
        self.received_messages: dict[str, Any] = {}
        self._connect_event = asyncio.Event()

    async def connect(self) -> None:
        """Connect to MQTT broker."""
        loop = asyncio.get_running_loop()
        self._connect_event.clear()

        if self._username:
            self._client.username_pw_set(self._username, self._password)

        self._client.connect(self._broker, self._port, 60)
        self._client.loop_start()

        # Wait for connection
        try:
            await asyncio.wait_for(self._connect_event.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            self._client.loop_stop()
            raise ConnectionError("MQTT connection timed out")

    async def disconnect(self) -> None:
        """Disconnect from MQTT broker."""
        self._client.loop_stop()
        self._client.disconnect()

    def _on_connect(self, client: mqtt.Client, userdata, flags, rc, properties=None):
        """Handle MQTT connection."""
        if rc == 0:
            _LOGGER.info("Connected to MQTT broker at %s:%d", self._broker, self._port)
            # Subscribe to all Firewalla topics
            topics = [
                f"{self._prefix}/{TOPIC_STATUS}",
                f"{self._prefix}/{TOPIC_LIVE_STATS}",
                f"{self._prefix}/{TOPIC_HOSTS_SUMMARY}",
                f"{self._prefix}/{TOPIC_HOSTS}",
                f"{self._prefix}/{TOPIC_HOST}/#",
                f"{self._prefix}/{TOPIC_ALARMS_SUMMARY}",
                f"{self._prefix}/{TOPIC_ALARMS}",
                f"{self._prefix}/{TOPIC_USAGE}",
                f"{self._prefix}/{TOPIC_SPEEDTEST}",
                f"{self._prefix}/{TOPIC_BOX_INFO}",
                f"{self._prefix}/{TOPIC_BOX_FEATURES}",
            ]
            for topic in topics:
                client.subscribe(topic, qos=1)
                _LOGGER.debug("Subscribed to %s", topic)
            self._connect_event.set()
        else:
            _LOGGER.error("MQTT connection failed with code %d", rc)

    def _on_message(self, client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
        """Handle incoming MQTT message."""
        try:
            payload = json.loads(msg.payload.decode())
            self.received_messages[msg.topic] = payload
            _LOGGER.debug("Received %s: %s", msg.topic, msg.payload.decode()[:200])
        except json.JSONDecodeError:
            _LOGGER.warning("Invalid JSON on %s: %s", msg.topic, msg.payload)

    def _on_disconnect(self, client: mqtt.Client, userdata, rc, properties=None):
        """Handle MQTT disconnection."""
        _LOGGER.warning("Disconnected from MQTT broker (rc=%d)", rc)

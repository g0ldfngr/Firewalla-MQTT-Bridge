"""Device tracker platform for Firewalla MQTT Bridge.

Provides presence detection for devices on the network based on
Firewalla's host tracking data.
"""

from __future__ import annotations

import logging

from homeassistant.components.device_tracker import ScannerEntity, SourceType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER, TOPIC_HOST
from .entity import FirewallaTopicEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up device tracker entities from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    coordinator = data["coordinator"]
    prefix = entry.data.get("mqtt_prefix", "firewalla")

    # Built via a coordinator listener rather than read once here — at initial
    # setup the retained MQTT hosts message may not have arrived yet, and new
    # devices can join the network at any time.
    known_macs: set[str] = set()

    @callback
    def _add_new_devices() -> None:
        hosts_data = (coordinator.data or {}).get(f"{prefix}/network/hosts", {})
        new_entities: list[ScannerEntity] = []
        for device in hosts_data.get("online", []):
            mac = device.get("mac", "")
            if not mac or mac in known_macs:
                continue
            known_macs.add(mac)
            mac_underscore = mac.replace(":", "_")
            new_entities.append(
                FirewallaDeviceTracker(
                    device_name=device.get("name", "Unknown"),
                    mac=mac,
                    mac_underscore=mac_underscore,
                    coordinator=coordinator,
                    device_id=coordinator._device_id,
                    client=client,
                    prefix=prefix,
                )
            )
        if new_entities:
            async_add_entities(new_entities)

    _add_new_devices()
    entry.async_on_unload(coordinator.async_add_listener(_add_new_devices))


class FirewallaDeviceTracker(FirewallaTopicEntity, ScannerEntity):
    """Router-based presence tracker for a network device.

    Must be a ScannerEntity, not TrackerEntity: TrackerEntity derives state
    from GPS/location (so is_connected is ignored and state stays "unknown")
    and forces a recorder write on every coordinator update, which floods the
    database because the coordinator updates on every MQTT message.

    ScannerEntity.unique_id returns mac_address, which would discard
    _attr_unique_id and detach these entities from their existing registry
    entries, so unique_id is overridden below to keep the original IDs.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        device_name: str,
        mac: str,
        mac_underscore: str,
        coordinator=None,
        client=None,
        prefix: str = "firewalla",
        device_id: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._device_name = device_name
        self._mac = mac
        self._mac_underscore = mac_underscore
        self._client = client
        self._prefix = prefix
        self._watched_topic = f"{prefix}/{TOPIC_HOST}/{mac_underscore}"
        self._attr_name = device_name
        self._attr_unique_id = f"firewalla_tracker_{mac_underscore}"
        self._attr_mac_address = mac
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, mac_underscore)},
            name=device_name,
            via_device_id=device_id,
        )

    @property
    def unique_id(self) -> str | None:
        """Keep the stable firewalla_tracker_<mac> ID (see class docstring)."""
        return self._attr_unique_id

    @property
    def source_type(self) -> SourceType:
        return SourceType.ROUTER

    @property
    def is_connected(self) -> bool | None:
        topic = f"{self._prefix}/{TOPIC_HOST}/{self._mac_underscore}"
        if self.coordinator.data is None:
            return None
        payload = self.coordinator.data.get(topic)
        if payload:
            return bool(payload.get("online"))
        return None

    @property
    def extra_state_attributes(self) -> dict:
        topic = f"{self._prefix}/{TOPIC_HOST}/{self._mac_underscore}"
        if self.coordinator.data is None:
            return None
        payload = self.coordinator.data.get(topic)
        if payload:
            # No "last_seen" here: Firewalla republishes every host roughly
            # every 30 s with a fresh timestamp, so it changed the attributes
            # (and wrote a recorder row) on every publish even when presence
            # and IP were unchanged.
            return {
                "ip_address": payload.get("ip"),
                "mac_address": self._mac,
            }
        return {"mac_address": self._mac}

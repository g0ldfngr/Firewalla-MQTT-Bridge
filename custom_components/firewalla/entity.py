"""Shared entity base for Firewalla MQTT Bridge."""

from __future__ import annotations

from typing import Any

from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

_UNSET: Any = object()


class FirewallaTopicEntity(CoordinatorEntity):
    """Coordinator entity that only refreshes when its own MQTT topic changes.

    The MQTT client pushes a coordinator update for every message on any
    Firewalla topic (several per second), and the coordinator data is a shallow
    copy of all received payloads. Without this filter every entity recomputes
    and writes its state on every message, which keeps the event loop busy and
    triggers "Updating state ... took N seconds" warnings.

    A topic's payload object is only replaced when that topic receives a new
    message, so an identity check on the payload is enough to detect changes.
    Subclasses set ``self._watched_topic`` in ``__init__``; entities without a
    topic (None) keep the default behaviour of refreshing on every update.
    """

    _watched_topic: str | None = None
    _last_payload: Any = _UNSET
    _last_available: bool | None = None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Write state only if this entity's payload or availability changed."""
        if self._watched_topic is None:
            super()._handle_coordinator_update()
            return
        payload = (self.coordinator.data or {}).get(self._watched_topic)
        available = self.coordinator.last_update_success
        if payload is self._last_payload and available == self._last_available:
            return
        self._last_payload = payload
        self._last_available = available
        super()._handle_coordinator_update()

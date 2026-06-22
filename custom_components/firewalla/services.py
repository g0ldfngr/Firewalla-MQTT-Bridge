"""Services for Firewalla MQTT Bridge."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
import voluptuous as vol

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SERVICE_RESCAN = "rescan"
SERVICE_RESCAN_SCHEMA = vol.Schema({})

SERVICE_FORCE_UPDATE = "force_update"
SERVICE_FORCE_UPDATE_SCHEMA = vol.Schema({})


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for Firewalla."""

    async def handle_rescan(call: ServiceCall) -> None:
        """Handle rescan service call."""
        _LOGGER.info("Firewalla rescan requested")
        for entry_id, data in hass.data.get(DOMAIN, {}).items():
            coordinator = data.get("coordinator")
            if coordinator:
                await coordinator.async_refresh()

    async def handle_force_update(call: ServiceCall) -> None:
        """Handle force update service call."""
        _LOGGER.info("Firewalla force update requested")
        for entry_id, data in hass.data.get(DOMAIN, {}).items():
            coordinator = data.get("coordinator")
            if coordinator:
                await coordinator.async_refresh()

    hass.services.async_register(
        DOMAIN, SERVICE_RESCAN, handle_rescan, schema=SERVICE_RESCAN_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_FORCE_UPDATE, handle_force_update, schema=SERVICE_FORCE_UPDATE_SCHEMA
    )


async def async_remove_services(hass: HomeAssistant) -> None:
    """Remove services for Firewalla."""
    hass.services.async_remove(DOMAIN, SERVICE_RESCAN)
    hass.services.async_remove(DOMAIN, SERVICE_FORCE_UPDATE)

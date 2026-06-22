"""Config flow for Firewalla MQTT Bridge."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_FIREWALLA_IP,
    CONF_MQTT_BROKER,
    CONF_MQTT_PASSWORD,
    CONF_MQTT_PORT,
    CONF_MQTT_PREFIX,
    CONF_MQTT_USERNAME,
    DEFAULT_MQTT_PORT,
    DEFAULT_MQTT_PREFIX,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_MQTT_BROKER, default="10.100.255.22"): str,
        vol.Required(CONF_MQTT_PORT, default=DEFAULT_MQTT_PORT): vol.Coerce(int),
        vol.Required(CONF_MQTT_PREFIX, default=DEFAULT_MQTT_PREFIX): str,
        vol.Required(CONF_MQTT_USERNAME, default=""): str,
        vol.Required(CONF_MQTT_PASSWORD, default=""): str,
        vol.Required(CONF_FIREWALLA_IP, default="10.100.255.1"): str,
    }
)


class FirewallaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Firewalla."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return the options flow."""
        return FirewallaOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initiated by the user."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        return self.async_create_entry(title="Firewalla", data=user_input)


class FirewallaOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is None:
            data = self.config_entry.data
            schema = vol.Schema(
                {
                    vol.Required(
                        CONF_MQTT_BROKER, default=data.get(CONF_MQTT_BROKER, "")
                    ): str,
                    vol.Required(
                        CONF_MQTT_PORT, default=data.get(CONF_MQTT_PORT, DEFAULT_MQTT_PORT)
                    ): vol.Coerce(int),
                    vol.Required(
                        CONF_MQTT_PREFIX, default=data.get(CONF_MQTT_PREFIX, DEFAULT_MQTT_PREFIX)
                    ): str,
                    vol.Required(
                        CONF_MQTT_USERNAME, default=data.get(CONF_MQTT_USERNAME, "")
                    ): str,
                    vol.Required(
                        CONF_MQTT_PASSWORD, default=data.get(CONF_MQTT_PASSWORD, "")
                    ): str,
                    vol.Required(
                        CONF_FIREWALLA_IP, default=data.get(CONF_FIREWALLA_IP, "")
                    ): str,
                }
            )
            return self.async_show_form(step_id="init", data_schema=schema)

        return self.async_create_entry(title="Firewalla", data=user_input)

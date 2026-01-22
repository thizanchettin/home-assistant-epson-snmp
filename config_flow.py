from __future__ import annotations
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_COMMUNITY,
    CONF_HOST,
    CONF_NAME,
    CONF_PROFILE,
    CONF_SCAN_INTERVAL,
    CONF_VERSION,
    DEFAULT_COMMUNITY,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_VERSION,
    DOMAIN,
    PROFILE_AUTO,
)
from .profile_loader import list_profile_ids

"""
Config flow for the Epson SNMP integration.

This module defines:
- The initial user setup flow (host, name, community, SNMP version, scan interval).
- The options flow to select a profile (including "auto").

Note: Connectivity validation is intentionally minimal here to keep setup fast and
avoid regressions. Runtime readiness is handled by the coordinator's first refresh.
"""


class EpsonSnmpConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Epson SNMP."""
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step where the user configures connection settings."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()

            # Unique ID based on host (can be upgraded to serial later if desired).
            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input.get(CONF_NAME) or DEFAULT_NAME,
                data={
                    CONF_HOST: host,
                    CONF_NAME: user_input.get(CONF_NAME, DEFAULT_NAME),
                    CONF_COMMUNITY: user_input.get(CONF_COMMUNITY, DEFAULT_COMMUNITY),
                    CONF_VERSION: user_input.get(CONF_VERSION, DEFAULT_VERSION),
                    CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                },
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Optional(CONF_COMMUNITY, default=DEFAULT_COMMUNITY): str,
                vol.Optional(CONF_VERSION, default=DEFAULT_VERSION): str,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    def async_get_options_flow(config_entry):
        """Return the options flow handler."""
        return EpsonSnmpOptionsFlowHandler(config_entry)


class EpsonSnmpOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for Epson SNMP (profile selection)."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self.entry = entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Manage the options (profile selection)."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        profiles = list_profile_ids(self.hass)
        current = self.entry.options.get(CONF_PROFILE, PROFILE_AUTO)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_PROFILE, default=current): vol.In(profiles),
                }
            ),
        )

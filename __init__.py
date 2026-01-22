from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    CONF_COMMUNITY,
    CONF_HOST,
    CONF_NAME,
    CONF_PROFILE,
    CONF_SCAN_INTERVAL,
    CONF_VERSION,
    DOMAIN,
    PROFILE_AUTO,
)
from .coordinator import EpsonSnmpCoordinator

"""
Epson SNMP integration entrypoints for Home Assistant.

This module wires the config entry lifecycle:
- async_setup_entry: initialize the coordinator and forward platforms.
- async_unload_entry: unload platforms and clean up stored state.

No network I/O should run directly in the event loop; the coordinator handles
SNMP polling safely outside the loop.
"""


PLATFORMS: list[str] = ["sensor"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration via YAML (not used; kept for HA compatibility)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Epson SNMP from a config entry."""
    host: str = entry.data[CONF_HOST]
    name: str = entry.data[CONF_NAME]
    community: str = entry.data[CONF_COMMUNITY]
    version: str = str(entry.data[CONF_VERSION]).lower()
    scan_seconds: int = int(entry.data[CONF_SCAN_INTERVAL])
    profile_id: str = entry.options.get(CONF_PROFILE, PROFILE_AUTO)

    # pysnmp mpModel: 0=v1, 1=v2c
    mp_model = 0 if version in ("1", "v1") else 1

    coordinator = EpsonSnmpCoordinator(
        hass,
        host=host,
        community=community,
        mp_model=mp_model,
        scan_interval_seconds=scan_seconds,
        name=name,
        profile_id=profile_id,
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        # HA expects ConfigEntryNotReady before forwarding platforms
        raise ConfigEntryNotReady(str(err)) from err

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry and clean up runtime listeners."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Remove coordinator
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)

        # Cleanup runtime listeners/state (supplies discovery)
        runtime_key = f"{DOMAIN}_runtime"
        runtime = hass.data.get(runtime_key, {})
        state = runtime.pop(entry.entry_id, None)
        if state:
            unsub = state.get("unsub")
            if callable(unsub):
                unsub()

        # opcional: se runtime ficar vazio, pode remover a chave
        if runtime_key in hass.data and not hass.data[runtime_key]:
            hass.data.pop(runtime_key, None)

    return unload_ok

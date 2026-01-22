from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pysnmp.hlapi.v3arch.asyncio import (
    CommunityData,
    ContextData,
    ObjectIdentity,
    ObjectType,
    SnmpEngine,
    UdpTransportTarget,
    get_cmd,
)

from .const import PROFILE_AUTO
from .profile_loader import load_profile, resolve_profile_id_auto


_LOGGER = logging.getLogger(__name__)


def _run_coro_in_new_loop(coro: Any) -> Any:
    """Run a coroutine in a new event loop (intended for executor threads)."""
    return asyncio.run(coro)


class EpsonSnmpCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinates periodic SNMP polling and exposes latest values to entities."""

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        host: str,
        community: str,
        mp_model: int,
        scan_interval_seconds: int,
        name: str,
        profile_id: str = PROFILE_AUTO,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{name} Coordinator",
            update_interval=timedelta(seconds=scan_interval_seconds),
        )
        self._host = host
        self._community = community
        self._mp_model = mp_model
        self._profile_id = profile_id
        self._profile = None  # ParsedProfile, loaded lazily

    async def async_get_profile(self):
        """
        Public accessor for the active ParsedProfile.

        This avoids platforms touching coordinator internals (_ensure_profile/_profile)
        while keeping behavior identical.
        """
        await self._ensure_profile()
        return self._profile

    async def _snmp_get_batch(self, oids: list[str]) -> list[Any]:
        async def _async_do() -> list[Any]:
            target = await UdpTransportTarget.create((self._host, 161), timeout=2, retries=1)

            err_ind, err_stat, _, var_binds = await get_cmd(
                SnmpEngine(),
                CommunityData(self._community, mpModel=self._mp_model),
                target,
                ContextData(),
                *[ObjectType(ObjectIdentity(oid)) for oid in oids],
                lookupMib=False,
            )
            if err_ind or err_stat:
                raise UpdateFailed(str(err_ind or err_stat))

            return [v for _, v in var_binds]

        def _do_sync() -> list[Any]:
            return _run_coro_in_new_loop(_async_do())

        return await self.hass.async_add_executor_job(_do_sync)

    async def _ensure_profile(self) -> None:
        if self._profile:
            return

        pid = self._profile_id
        if pid == PROFILE_AUTO:
            pid = await resolve_profile_id_auto(
                self.hass,
                host=self._host,
                community=self._community,
                mp_model=self._mp_model,
            )

        self._profile = await load_profile(self.hass, pid)

    async def _async_update_data(self) -> dict[str, Any]:
        await self._ensure_profile()

        if not self._profile.oids:
            raise UpdateFailed("Profile has no sources/OIDs defined")

        data: dict[str, Any] = {}

        keys = list(self._profile.oids.keys())
        oids = list(self._profile.oids.values())
        values = await self._snmp_get_batch(oids)

        for k, v in zip(keys, values):
            data[k] = str(v)

        if not data.get("firmware"):
            fw = data.get("firmware_code_raw")
            if fw:
                data["firmware"] = fw

        supplies_cfg = self._profile.supplies or {}
        if supplies_cfg.get("enabled"):
            out = []
            probe = supplies_cfg.get("probe") or {}
            level = supplies_cfg.get("level") or {}

            index_prefix = supplies_cfg.get("index_prefix")
            if index_prefix is None:
                index_prefix = probe.get(
                    "index_prefix") or level.get("index_prefix")

            def _idx_oid(base: str, idx: int) -> str:
                """Build an indexed OID supporting optional two-level indexes."""
                if index_prefix is None:
                    return f"{base}.{idx}"
                return f"{base}.{index_prefix}.{idx}"

            for i in range(1, 9):
                try:
                    desc = (await self._snmp_get_batch([_idx_oid(probe["desc_oid"], i)]))[0]
                except Exception:
                    break

                if not desc:
                    break

                entry = {
                    "index": i,
                    "desc": str(desc),
                    "color": None,
                    "level": None,
                    "max": None,
                }

                if "color_oid" in probe:
                    try:
                        entry["color"] = str(
                            (await self._snmp_get_batch([_idx_oid(probe["color_oid"], i)]))[0]
                        )
                    except Exception:
                        pass

                if "value_oid" in level and "max_oid" in level:
                    try:
                        entry["level"] = str(
                            (await self._snmp_get_batch([_idx_oid(level["value_oid"], i)]))[0]
                        )
                        entry["max"] = str(
                            (await self._snmp_get_batch([_idx_oid(level["max_oid"], i)]))[0]
                        )
                    except Exception:
                        pass

                out.append(entry)

            data["supplies"] = out

        return data

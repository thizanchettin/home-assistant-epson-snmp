from __future__ import annotations

"""
Profile loading and auto-detection utilities for the Epson SNMP integration.

This module:
- Lists available profile IDs (embedded and user overrides).
- Loads and parses YAML profiles into a normalized Python structure.
- Implements the "auto" profile selection using a probe + scoring mechanism.

All SNMP probing is executed outside Home Assistant's event loop by delegating
work to an executor thread and running a dedicated asyncio loop there.
"""

import asyncio
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.util.yaml import load_yaml
from pysnmp.hlapi.v3arch.asyncio import (
    CommunityData,
    ContextData,
    ObjectIdentity,
    ObjectType,
    SnmpEngine,
    UdpTransportTarget,
    get_cmd,
)

from .const import PROFILE_AUTO, PROFILE_GENERIC
from .profile_parser import ParsedProfile, parse_profile


def _match(op: str, actual: Any, expected: Any) -> bool:
    """Evaluate a detection rule condition."""
    if actual is None:
        return False
    a = str(actual)
    e = str(expected)
    if op == "equals":
        return a == e
    if op == "contains_ci":
        return e.lower() in a.lower()
    if op == "exists":
        return True
    return False


def _run_coro_in_new_loop(coro: Any) -> Any:
    """Run a coroutine in a new event loop (intended for executor threads)."""
    return asyncio.run(coro)


async def _snmp_probe(
    hass: HomeAssistant,
    host: str,
    community: str,
    mp_model: int,
    probe: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Execute a one-shot SNMP GET for a set of probe OIDs and return a dict
    keyed by the probe items' "key" entries.

    Returns an empty dict on errors/timeouts to keep auto-detection resilient.
    """
    oids = [p["oid"] for p in probe]

    async def _async_do() -> list[Any]:
        target = await UdpTransportTarget.create((host, 161), timeout=2, retries=1)

        err_ind, err_stat, _, var_binds = await get_cmd(
            SnmpEngine(),
            CommunityData(community, mpModel=mp_model),
            target,
            ContextData(),
            *[ObjectType(ObjectIdentity(oid)) for oid in oids],
            lookupMib=False,
        )
        if err_ind or err_stat:
            return []
        return [v for _, v in var_binds]

    def _do_sync() -> list[Any]:
        return _run_coro_in_new_loop(_async_do())

    values = await hass.async_add_executor_job(_do_sync)
    if not values:
        return {}

    out: dict[str, Any] = {}
    for p, v in zip(probe, values):
        out[p["key"]] = str(v)
    return out


def _embedded_dir() -> Path:
    """Return the directory containing built-in profiles shipped with the integration."""
    return Path(__file__).parent / "profiles"


def _override_dir(hass: HomeAssistant) -> Path:
    """Return the directory where users can override profiles in /config."""
    return Path(hass.config.path("epson_snmp", "profiles"))


def list_profile_ids(hass: HomeAssistant) -> list[str]:
    """
    List available profile IDs from both embedded and override directories.

    The special "auto" profile is always inserted first.
    """
    ids = set()

    for p in _embedded_dir().glob("*.yaml"):
        ids.add(p.stem)

    od = _override_dir(hass)
    if od.exists():
        for p in od.glob("*.yaml"):
            ids.add(p.stem)

    out = sorted(ids, key=lambda s: s.lower())
    if PROFILE_AUTO in out:
        out.remove(PROFILE_AUTO)
    out.insert(0, PROFILE_AUTO)
    return out


async def _load_yaml_file(hass: HomeAssistant, path: Path) -> dict[str, Any]:
    """Load YAML from disk using an executor to avoid blocking the event loop."""
    return await hass.async_add_executor_job(load_yaml, str(path)) or {}


async def load_profile(hass: HomeAssistant, profile_id: str) -> ParsedProfile:
    """
    Load a profile by ID and parse it into a normalized structure.

    Override precedence:
      1) /config/epson_snmp/profiles/<id>.yaml
      2) custom_components/epson_snmp/profiles/<id>.yaml
    """
    od = _override_dir(hass) / f"{profile_id}.yaml"
    if od.exists():
        return parse_profile(await _load_yaml_file(hass, od))

    ed = _embedded_dir() / f"{profile_id}.yaml"
    if ed.exists():
        return parse_profile(await _load_yaml_file(hass, ed))

    raise ValueError(f"Profile not found: {profile_id}")


async def resolve_profile_id_auto(
    hass: HomeAssistant,
    *,
    host: str,
    community: str,
    mp_model: int,
) -> str:
    """
    Select the best matching profile for a device using probe + scoring rules.

    - Evaluates all profiles that define a "detection" section (excluding "auto").
    - Applies "required" rules strictly.
    - Falls back to PROFILE_GENERIC when no candidate passes threshold.
    """
    candidates: list[ParsedProfile] = []
    for pid in list_profile_ids(hass):
        if pid == PROFILE_AUTO:
            continue
        try:
            prof = await load_profile(hass, pid)
        except Exception:
            continue
        if not prof.detection:
            continue
        candidates.append(prof)

    best_id = PROFILE_GENERIC
    best_score = 0

    for prof in candidates:
        det = prof.detection or {}
        probe = det.get("probe") or []
        scoring = det.get("scoring") or {}
        rules = scoring.get("rules") or []
        threshold = int(scoring.get("threshold") or 0)

        values = await _snmp_probe(
            hass,
            host=host,
            community=community,
            mp_model=mp_model,
            probe=probe,
        )
        if not values:
            continue

        score = 0
        failed_required = False

        for r in rules:
            when = r.get("when") or {}
            key = when.get("key")
            op = when.get("op")
            val = when.get("value")
            required = bool(r.get("required"))
            s = int(r.get("score") or 0)

            if _match(op, values.get(key), val):
                score += s
            elif required:
                failed_required = True
                break

        if failed_required:
            continue

        if score >= threshold and score > best_score:
            best_score = score
            best_id = prof.meta.id

    return best_id

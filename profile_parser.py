from __future__ import annotations

"""
YAML profile parsing for the Epson SNMP integration.

This module defines the in-memory representation of a profile and converts raw
YAML dictionaries into strongly-typed dataclasses.

Supported YAML schemas (backwards compatible):
- Legacy:  oids: {key: "1.3.6...."}
- Current: sources: {key: {oid: "1.3.6....", kind: "..."}}

Only the OID string is required at runtime for polling; additional metadata is
kept to support future extensions while keeping the parser strict and predictable.
"""

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass


_DEVICE_CLASS = {
    "duration": SensorDeviceClass.DURATION,
}

_STATE_CLASS = {
    "measurement": SensorStateClass.MEASUREMENT,
    "total_increasing": SensorStateClass.TOTAL_INCREASING,
}

_ALLOWED_KINDS = {
    "int",
    "str",
    "timeticks_seconds",
    "mapped_int",
    "ratio_percent",
}


@dataclass(frozen=True)
class ProfileMeta:
    """Profile metadata used for identification and UI labels."""
    id: str
    name: str
    priority: int
    match_model: list[str]


@dataclass(frozen=True)
class SensorDef:
    """Definition of a sensor entity to be created from a YAML profile."""
    key: str
    name_suffix: str
    kind: str
    source: str | None = None           # key in oids/sources
    # literal OID override (quick escape hatch)
    oid: str | None = None
    icon: str | None = None
    unit: str | None = None
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = None
    map: dict[str, str] | None = None
    default: str | None = None
    numerator: str | None = None        # key in oids (ratio)
    denominator: str | None = None      # key in oids (ratio)


@dataclass(frozen=True)
class ParsedProfile:
    """Fully parsed profile used by the coordinator and platforms."""
    meta: ProfileMeta
    oids: dict[str, str]
    sensors: list[SensorDef]
    detection: dict[str, Any] | None
    supplies: dict[str, Any] | None


def _resolve_oid_value(v: Any) -> str:
    """Normalize a raw YAML value into a clean OID string."""
    return str(v).strip()


def parse_profile(raw: dict[str, Any]) -> ParsedProfile:
    """
    Parse a raw YAML dict into a ParsedProfile.

    Expected top-level keys:
    - profile: {id, name?, priority?, match_model?}
    - oids or sources: mapping defining OID strings
    - sensors: list defining entity mappings
    - detection: optional auto-detection section
    - supplies: optional supplies section (ink/toner probes)

    Raises:
        ValueError: when required fields are missing or invalid.
    """
    p = raw.get("profile") or {}
    pid = str(p.get("id") or "").strip()
    if not pid:
        raise ValueError("profile.id is required")

    name = str(p.get("name") or pid).strip()
    priority = int(p.get("priority") or 0)

    match_model = p.get("match_model") or []
    match_model = [str(x) for x in match_model]

    # Backwards compatibility: accept legacy "oids" or current "sources"
    oids_raw = raw.get("oids") or raw.get("sources") or {}
    oids: dict[str, str] = {}

    for k, v in oids_raw.items():
        if isinstance(v, dict):
            # current schema: sources: {key: {oid: "...", kind: "..."}}
            oid_val = str(v.get("oid") or "").strip()
            if oid_val:
                oids[str(k)] = oid_val
        else:
            # legacy schema: oids: {key: "1.3...."}
            oid_val = _resolve_oid_value(v)
            if oid_val:
                oids[str(k)] = oid_val

    sensors_raw = raw.get("sensors") or []
    sensors: list[SensorDef] = []

    for s in sensors_raw:
        kind = str(s.get("kind") or "").strip()
        if kind not in _ALLOWED_KINDS:
            raise ValueError(f"Invalid kind: {kind}")

        dc = s.get("device_class")
        sc = s.get("state_class")

        sensors.append(
            SensorDef(
                key=str(s["key"]),
                name_suffix=str(s["name_suffix"]),
                kind=kind,
                source=s.get("source") or s.get("source_key"),
                oid=s.get("oid"),
                icon=s.get("icon"),
                unit=s.get("unit"),
                device_class=_DEVICE_CLASS.get(dc) if dc else None,
                state_class=_STATE_CLASS.get(sc) if sc else None,
                map=s.get("map"),
                default=s.get("default"),
                numerator=s.get("numerator"),
                denominator=s.get("denominator"),
            )
        )

    detection = raw.get("detection")
    supplies = raw.get("supplies")

    return ParsedProfile(
        meta=ProfileMeta(
            id=pid,
            name=name,
            priority=priority,
            match_model=match_model,
        ),
        oids=oids,
        sensors=sensors,
        detection=detection,
        supplies=supplies,
    )

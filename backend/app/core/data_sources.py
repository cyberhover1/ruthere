"""Activity data-source identifiers (PRD §4.1).

These are the 7 sensor/system sources the frontend detects. They are stored as
comma-separated strings in `friend_data_sources.allowed_sources` and used to
compute per-friend visible activity in M9.
"""

from __future__ import annotations

STEPS = "steps"
SCREEN_UNLOCK = "screen_unlock"
CHARGING = "charging"
HEADSET = "headset"
PICKUP_FLIP = "pickup_flip"
AMBIENT_LIGHT = "ambient_light"
SIGNIFICANT_MOTION = "significant_motion"

ALL_DATA_SOURCES: tuple[str, ...] = (
    STEPS,
    SCREEN_UNLOCK,
    CHARGING,
    HEADSET,
    PICKUP_FLIP,
    AMBIENT_LIGHT,
    SIGNIFICANT_MOTION,
)


def is_valid_source(source: str) -> bool:
    return source in ALL_DATA_SOURCES


def serialize(sources: list[str]) -> str:
    """Join a source list into the storage string (order preserved, deduped)."""
    seen: set[str] = set()
    out: list[str] = []
    for s in sources:
        if s in ALL_DATA_SOURCES and s not in seen:
            seen.add(s)
            out.append(s)
    return ",".join(out)


def deserialize(stored: str) -> list[str]:
    """Split the storage string back into a source list."""
    return [s for s in stored.split(",") if s]

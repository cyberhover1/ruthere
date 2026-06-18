"""Activity computation engine (PRD §4.2 / §4.3).

Turns raw per-source component values (0..1) into a 0..100 activity integer.
The key feature: a user can show *different* values to different friends by
restricting which sources are visible — `compute_visible_for_friend` recomputes
using only the allowed subset, re-normalizing weights so they still sum to 1.

Default weights (PRD §4.3):
  steps 40% · screen_unlock 20% · significant_motion 15%
  charging+headset 10% (5% each) · pickup_flip 10% · ambient_light 5%
"""

from __future__ import annotations

from app.core.config import settings
from app.core.data_sources import ALL_DATA_SOURCES

# PRD §4.3 default contribution weights (fractions summing to 1.0).
DEFAULT_WEIGHTS: dict[str, float] = {
    "steps": 0.40,
    "screen_unlock": 0.20,
    "significant_motion": 0.15,
    "charging": 0.05,
    "headset": 0.05,
    "pickup_flip": 0.10,
    "ambient_light": 0.05,
}


def _clamp_unit(x: float) -> float:
    return max(0.0, min(1.0, x))


def _weighted_sum(components: dict[str, float], weights: dict[str, float]) -> float:
    total = 0.0
    for source, weight in weights.items():
        val = components.get(source)
        if val is not None:
            total += weight * _clamp_unit(val)
    return total


def compute_activity(
    components: dict[str, float], weights: dict[str, float] | None = None
) -> int:
    """Compute an overall 0..100 activity value from raw components."""
    w = weights if weights is not None else DEFAULT_WEIGHTS
    score = _weighted_sum(components, w)
    return _to_int(score)


def compute_visible_for_friend(
    components: dict[str, float],
    allowed_sources: list[str],
    weights: dict[str, float] | None = None,
) -> int:
    """Compute the 0..100 value visible to a friend who only sees `allowed_sources`.

    Uses only the allowed subset of sources and re-normalizes their weights to
    sum to 1, so the friend's view reflects activity derived solely from what
    they're permitted to see (PRD §4.2).
    """
    w = weights if weights is not None else DEFAULT_WEIGHTS
    subset_weights = {s: w[s] for s in allowed_sources if s in w}
    weight_sum = sum(subset_weights.values())
    if weight_sum <= 0:
        # No allowed sources contribute -> friend sees nothing active.
        return 0
    normalized = {s: v / weight_sum for s, v in subset_weights.items()}
    score = _weighted_sum(components, normalized)
    return _to_int(score)


def _to_int(score: float) -> int:
    return max(0, min(settings.activity_max_value, round(score * settings.activity_max_value)))


__all__ = [
    "DEFAULT_WEIGHTS",
    "ALL_DATA_SOURCES",
    "compute_activity",
    "compute_visible_for_friend",
]

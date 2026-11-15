"""Small pure pre-update EWMA primitive; callers own observation deduplication."""
from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Baseline:
    mean: float = 0.0
    variance: float = 0.0
    count: int = 0
    version: str = "ewma-bucket-10s-v1"
    seeded: bool = False

    def __post_init__(self) -> None:
        if not math.isfinite(self.mean) or not -1 <= self.mean <= 1:
            raise ValueError("baseline mean must be finite and within [-1, 1]")
        if not math.isfinite(self.variance) or self.variance < 0 or self.count < 0:
            raise ValueError("baseline variance/count must be nonnegative")


@dataclass(frozen=True)
class Normalized:
    absolute: float
    z: float | None
    previous: Baseline
    updated: Baseline
    status: str


def normalize(
    value: float,
    baseline: Baseline,
    *,
    bucket_seconds: float = 10,
    time_constant: float = 180,
    warmup: int = 20,
    std_floor: float = 0.10,
    z_clip: float = 4,
) -> Normalized:
    """Score before updating exactly one valid regular bucket.

    Missing buckets must not call this function. A repeated publication is not
    a bucket; callers rebuild from unique observations instead of applying it.
    """
    if not math.isfinite(value) or not -1 <= value <= 1:
        raise ValueError("normalization requires an attributable finite score")
    if min(bucket_seconds, time_constant, std_floor, z_clip) <= 0 or warmup < 0:
        raise ValueError("normalization settings must be positive")
    delta = value - baseline.mean
    ready = baseline.seeded or baseline.count >= warmup
    z = max(-z_clip, min(z_clip, delta / max(math.sqrt(baseline.variance), std_floor))) if ready else None
    alpha = -math.expm1(-bucket_seconds / time_constant)
    updated = Baseline(
        mean=baseline.mean + alpha * delta,
        variance=(1 - alpha) * (baseline.variance + alpha * delta * delta),
        count=baseline.count + 1,
        version=baseline.version,
        seeded=baseline.seeded,
    )
    return Normalized(value, z, baseline, updated, "seeded_fixture" if baseline.seeded else "ready" if ready else "warming_up")

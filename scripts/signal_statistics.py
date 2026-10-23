"""Descriptive Wilson uncertainty bounds for binary directional matches."""
from math import sqrt


def wilson_interval(matches, total, z=1.959963984540054):
    """Return 95% Wilson score interval; not adjusted for serial dependence."""
    if (type(matches) is not int or type(total) is not int or
            total <= 0 or not 0 <= matches <= total):
        return None
    p = matches / total
    z2 = z * z
    denom = 1 + z2 / total
    centre = (p + z2 / (2 * total)) / denom
    half = z * sqrt(p * (1 - p) / total + z2 / (4 * total * total)) / denom
    return max(0, centre - half), min(1, centre + half)


def descriptive_confidence(matches, total, min_samples=30):
    """Label sample adequacy, never assert predictive significance."""
    interval = wilson_interval(matches, total)
    if interval is None or total < min_samples:
        return {"status": "insufficient", "interval": None}
    return {"status": "descriptive_only", "interval": interval}

"""Freeze original market routes and level checks; no trade or position tracking."""
try:
    from .swing_scenarios import build_swing_scenarios
except ImportError:
    from swing_scenarios import build_swing_scenarios


def freeze(record):
    return build_swing_scenarios({'measurements':[record]},record['finished_at'])

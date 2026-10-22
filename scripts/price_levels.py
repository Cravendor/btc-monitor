"""Price-level calculations. Logarithmic price levels require positive prices."""
from math import exp, log, isfinite

RATIOS = (0.236, 0.382, 0.5, 0.618, 0.786)


def retracements(low, high, *, method="log", ratios=RATIOS):
    low, high = float(low), float(high)
    if not all(isfinite(v) for v in (low, high)) or low <= 0 or high <= low:
        raise ValueError("require finite positive low < high")
    if method not in ("log", "linear"):
        raise ValueError("unknown method")
    result = []
    for ratio in ratios:
        ratio = float(ratio)
        if not isfinite(ratio) or not 0 <= ratio <= 1:
            raise ValueError("ratio must be between zero and one")
        if method == "linear":
            value = high - ratio * (high - low)
        else:
            value = exp(log(high) - ratio * (log(high) - log(low)))
        result.append({"ratio": ratio, "price": round(value, 8)})
    return {"method": method, "low": low, "high": high, "levels": result}

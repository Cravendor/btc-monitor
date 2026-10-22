"""Explain provisional BTC 4H price signals beside derivatives context.

No uncalibrated derivative data can change the directional grade.
"""
def combine_context(price_result, derivatives=None):
    if price_result.get("status") != "provisional":
        return {"status": "unavailable", "grade": None,
                "reason": "price assessment unavailable"}
    if price_result.get("confidence") != "low":
        raise ValueError("unexpected strategy confidence")
    result = {
        "status": "provisional", "grade": price_result["grade"],
        "confidence": "low", "price_score": price_result["score"],
        "price_vs_20_prior_pct": price_result.get("price_vs_20_prior_pct"),
        "volume_ratio": price_result.get("volume_ratio"),
        "funding_rate": None, "open_interest": None, "oi_change_pct": None,
        "derivatives_status": "unavailable",
        "cvd_status": "unavailable",
        "hypothesis_a": "not_evaluated", "hypothesis_b": "not_evaluated",
        "reason": "Price trend provisional; derivatives descriptive only"
    }
    if derivatives and derivatives.get("status") == "context_only":
        result["funding_rate"] = derivatives.get("funding_rate")
        result["open_interest"] = derivatives.get("open_interest")
        result["oi_change_pct"] = derivatives.get("oi_change_pct")
        result["derivatives_status"] = "context_only"
    return result

"""Audit frozen BTC directional predictions against observed outcomes.

No learning or live trading. This module summarizes only evaluations whose
source prediction was issued before its evaluation horizon. Missing/flat
outcomes are excluded from directional hit-rate denominators.
"""
from collections import defaultdict
from math import sqrt
from scripts.market_outcomes import evaluate_direction


def summarize_predictions(pairs):
    """pairs: sequence of {'prediction': {...}, 'outcome': {...}}.

    Returns grouped metrics by model version, horizon and market. Distinguishes
    unavailable, flat, correct, incorrect. Does not treat a hit rate as proof of
    predictive skill; baselines and out-of-sample testing are still required.
    """
    groups = defaultdict(list)
    for item in pairs:
        prediction = item["prediction"]
        result = evaluate_direction(prediction, item["outcome"])
        key = (prediction["model_version"], prediction["horizon_hours"],
               prediction["market"])
        groups[key].append(result)
    reports = []
    for (version, horizon, market), results in sorted(groups.items()):
        correct = sum(x.get("verdict") == "correct" for x in results)
        incorrect = sum(x.get("verdict") == "incorrect" for x in results)
        flat = sum(x.get("verdict") == "flat" for x in results)
        unavailable = sum(x["status"] == "unavailable" for x in results)
        n = correct + incorrect
        hit_rate = correct / n if n else None
        # Wilson interval (95%); descriptive only, not independence-adjusted.
        interval = None
        if n:
            z = 1.96
            denom = 1 + z*z/n
            center = (hit_rate + z*z/(2*n))/denom
            half = z*sqrt(hit_rate*(1-hit_rate)/n + z*z/(4*n*n))/denom
            interval = [round(center-half, 4), round(center+half, 4)]
        reports.append({
            "model_version": version, "horizon_hours": horizon, "market": market,
            "total": len(results), "correct": correct, "incorrect": incorrect,
            "flat": flat, "unavailable": unavailable,
            "directional_sample": n,
            "hit_rate": round(hit_rate, 4) if hit_rate is not None else None,
            "wilson_95_descriptive": interval,
            "caution": "No independence correction, no baseline or out-of-sample proof"
        })
    return reports

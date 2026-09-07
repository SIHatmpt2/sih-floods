from math import isfinite


def clamp(value, low=0.0, high=100.0):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return low
    if not isfinite(number):
        return low
    return max(low, min(high, number))


def linear_score(value, low, high):
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if high <= low:
        return 0.0
    return clamp((value - low) * 100.0 / (high - low))


def risk_level(score):
    score = clamp(score)
    if score >= 75:
        return "severe"
    if score >= 50:
        return "high"
    if score >= 25:
        return "moderate"
    return "low"

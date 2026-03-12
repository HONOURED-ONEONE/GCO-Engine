import math

def rolling_variance(series: list) -> float:
    if len(series) < 2:
        return 0.0
    mean = sum(series) / len(series)
    var = sum((x - mean)**2 for x in series) / (len(series) - 1)
    return var

def anomaly_density(items: list) -> float:
    if not items:
        return 0.0
    anom = sum(1 for i in items if i.get("quality_deviation", False))
    return anom / len(items)

def combine(var_norm: float, density: float, n_eff: int) -> float:
    base = var_norm + density
    if n_eff > 0:
        base += 1.0 / math.sqrt(n_eff)
    return min(0.9, max(0.0, base))

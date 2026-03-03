from app.api.utils.io import read_json, write_json, KPI_STORE_FILE
from app.api.services.corridor import propose_corridor_change

def maybe_propose_update():
    kpis = read_json(KPI_STORE_FILE).get("items", [])
    if len(kpis) < 3:
        return None

    recent = kpis[-3:]
    avg_energy = sum(k["energy_kwh"] for k in recent) / 3.0
    quality_issues = any(k["quality_deviation"] for k in recent)
    avg_yield = sum(k["yield_pct"] for k in recent) / 3.0

    # Rule 1: Tighten if energy is low and quality is good
    if avg_energy < 50.0 and not quality_issues:
        delta = {"temperature_upper": -0.5}
        evidence = "Last 3 batches showed consistently low energy and perfect quality. Proposing to tighten temperature upper bound."
        return propose_corridor_change(delta, evidence)

    # Rule 2: Widen if quality issues or low yield
    if quality_issues or avg_yield < 85.0:
        delta = {"temperature_lower": -1.0, "temperature_upper": 1.0}
        evidence = "Recent quality deviations or yield drops detected. Proposing to widen temperature corridor for more process flexibility."
        return propose_corridor_change(delta, evidence)

    return None

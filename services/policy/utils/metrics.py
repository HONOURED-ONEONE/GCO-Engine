import time

metrics = {
    "start_time": time.time(),
    "calls_total": 0,
    "proposals_total": 0,
    "proposed_cost_shaping_total": 0,
    "proposed_corridor_total": 0,
    "uncertainty_avg": 0.0,
    "restraint_rate": 0.0,
    "trust_score_avg": 0.0,
    "governance_post_failures": 0,
    "twin_cf_failures": 0,
    "store_sizes": 0,
    "last_proposal_id": None,
    "last_confidence": None
}

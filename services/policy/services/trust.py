from ..clients.governance_client import list_proposals
from ..utils.metrics import metrics

def compute_trust_score() -> float:
    try:
        props = list_proposals(limit=10)
    except:
        props = []
        
    if not props:
        return 0.8
        
    approved = sum(1 for p in props if p.get("status") == "approved")
    rejected = sum(1 for p in props if p.get("status") == "rejected")
    
    total = approved + rejected
    if total == 0:
        return 0.8
        
    score = 0.5 + 0.5 * (approved / total)
    metrics["trust_score_avg"] = score
    return min(1.0, max(0.5, score))

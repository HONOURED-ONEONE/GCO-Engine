import re
from typing import Dict, List, Any

def extract_numbers(text: str) -> List[float]:
    # Simple regex to extract numbers, ignoring things that might look like dates or non-relevant digits
    # Just grab anything looking like a float/int, maybe preceded by a minus sign
    matches = re.findall(r'-?\d+\.?\d*', text)
    nums = []
    for m in matches:
        try:
            nums.append(float(m))
        except ValueError:
            pass
    return nums

def check_numbers_in_text(narrative_text: str, evidence_metrics: Dict[str, float], tolerances: Dict[str, float]) -> List[Dict[str, Any]]:
    # A simple checker that sees if a number mentioned in text makes sense.
    # We will look for numbers that exceed known metrics + tolerances.
    issues = []
    text_nums = extract_numbers(narrative_text)
    
    # We want to map numbers back to fields, which is hard statically.
    # Instead, let's just do a naive check: if a number in text is larger than any metric + tolerance (or smaller than metric - tolerance for negatives)
    # This is a basic implementation for the claim checker.
    
    # We will simulate a robust claim checker by assuming any number not close to ANY known metric is an overclaim
    # if it's outside the tolerance range of all metrics.
    # For a real implementation, you would need LLM mapping.
    
    if not text_nums:
        return issues
        
    for num in text_nums:
        # Ignore small integers often used for counts or percentages (e.g., 0, 1, 100)
        if num in [0, 0.0, 1, 1.0, 100, 100.0]:
            continue
            
        found_match = False
        closest_field = None
        closest_metric = None
        min_diff = float('inf')
        
        for field, val in evidence_metrics.items():
            if isinstance(val, (int, float)):
                diff = abs(val - num)
                if diff < min_diff:
                    min_diff = diff
                    closest_field = field
                    closest_metric = val
                
                tol = tolerances.get(field, 0.0)
                if diff <= tol:
                    found_match = True
                    break
                    
        if not found_match and closest_field is not None:
            # Check if there's any tolerance exceeded
            tol = tolerances.get(closest_field, 0.0)
            if min_diff > tol:
                issues.append({
                    "type": "overclaim",
                    "field": closest_field,
                    "claimed": num,
                    "actual": closest_metric,
                    "tolerance": tol
                })
                
    return issues

def check_forbidden_phrases(narrative_text: str, phrases: List[str]) -> List[str]:
    found = []
    text_lower = narrative_text.lower()
    for phrase in phrases:
        if phrase.lower() in text_lower:
            found.append(phrase)
    return found

def build_safety_report(issues: List[Dict[str, Any]], forbidden: List[str], unknown_refs: bool = False) -> Dict[str, Any]:
    risk = "low"
    if len(issues) > 0 or len(forbidden) > 0 or unknown_refs:
        risk = "medium"
    if len(issues) > 2 or len(forbidden) > 1:
        risk = "high"
        
    return {
        "data_usage_ok": len(issues) == 0 and len(forbidden) == 0 and not unknown_refs,
        "hallucination_risk": risk,
        "overclaim_items": issues
    }

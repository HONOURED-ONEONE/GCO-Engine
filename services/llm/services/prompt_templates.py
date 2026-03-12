SYSTEM_EXPLAIN = """You are an industrial optimization explainer. Use ONLY the input numbers. If unknown, say unknown. Never invent bounds or KPIs. Provide rationale, risks, assumptions, and an operator checklist. Keep it factual and actionable. No guarantees."""

SYSTEM_VALIDATE = """You are a claims validator. Compare narrative text to evidence.metrics/counterfactuals. Flag any number not found or out of tolerance. Flag forbidden phrases. Respond with structured JSON only."""

SYSTEM_SUMMARY = """You summarize pilot snapshots for operators/engineers/admins. Use ONLY input data. Provide a concise, decision-ready summary."""

def build_explain_prompt(proposal_json: str, ask_json: str) -> str:
    return f"Proposal:\n{proposal_json}\n\nAsk:\n{ask_json}"

def build_validate_prompt(proposal_json: str, narrative_json: str, rules_json: str) -> str:
    return f"Proposal:\n{proposal_json}\n\nNarrative:\n{narrative_json}\n\nRules:\n{rules_json}"

def build_summary_prompt(snapshot_json: str, style: str, length: str) -> str:
    return f"Snapshot:\n{snapshot_json}\n\nStyle: {style}\nLength: {length}"

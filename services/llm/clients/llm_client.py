import os
import json
import asyncio
from typing import Optional, Dict, Any

PROVIDER = os.environ.get("PROVIDER", "gemini")
MODEL_ID = os.environ.get("MODEL_ID", "gemini-1.5-pro")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "unset")
LLM_TIMEOUT = int(os.environ.get("LLM_TIMEOUT", "20"))
LLM_MAX_TOKENS = int(os.environ.get("LLM_MAX_TOKENS", "1200"))
LLM_TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.2"))
LLM_DETERMINISTIC = os.environ.get("LLM_DETERMINISTIC", "true").lower() == "true"

class LLMClient:
    async def complete(self, system_prompt: str, user_prompt: str, json_schema_hint: Optional[Dict] = None) -> Dict[str, Any]:
        if LLM_DETERMINISTIC:
            # Deterministic stub returning seeded responses based on the request content
            # This handles explain, validate, and summary cases based on simple keyword heuristics
            text = "{}"
            if "explain" in system_prompt.lower() or "rationale" in json_schema_hint.get("properties", {}):
                text = json.dumps({
                    "rationale": "Tightening temperature bound improves energy efficiency.",
                    "risks": ["Potential yield drop if temperature too low"],
                    "assumptions": ["Cooling system behaves linearly"],
                    "operator_checklist": ["Verify KPI window", "Check bounds"]
                })
            elif "validator" in system_prompt.lower() or "validator" in user_prompt.lower() or "validation" in system_prompt.lower():
                text = json.dumps({
                    "status": "warn",
                    "issues": [
                        {"type": "overclaim", "field": "energy_delta_pct", "claimed": -5.0, "actual": -3.8, "tolerance": 0.2}
                    ],
                    "forbidden": ["guarantee"]
                })
            elif "summarize" in system_prompt.lower() or "summary" in system_prompt.lower() or "sections" in json_schema_hint.get("properties", {}):
                text = json.dumps({
                    "title": "Pilot snapshot — v3",
                    "bullets": ["Active version v3 with tightened upper temperature bound 154.5°C.", "Energy trending down across last 2 batches; no quality deviations observed."],
                    "sections": {
                        "overview": "Overview text",
                        "kpi_highlights": "Highlights",
                        "risks": "No current risks",
                        "next_steps": "Monitor"
                    }
                })
            else:
                text = json.dumps({})

            return {"text": text, "raw": {"mock": True}}

        # For a real provider, you would integrate with their SDK here.
        # Handling the exponential backoff:
        retries = 2
        for i in range(retries + 1):
            try:
                # Mock actual call
                await asyncio.sleep(0.1)
                return {"text": "{}", "raw": {}}
            except Exception as e:
                if i == retries:
                    raise e
                await asyncio.sleep(2 ** i)

        return {"text": "{}", "raw": {}}

llm_client = LLMClient()

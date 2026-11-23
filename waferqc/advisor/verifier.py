import json
from typing import Dict, Any, List, Tuple, Optional

REQUIRED_KEYS = {
    "analysis",
    "root_cause_hypothesis",
    "recommended_action",
    "disposition",
    "cited_sop_ids",
    "confidence_note"
}

BANNED_WORDS = {"kill", "destroy", "weapon", "hack", "bomb", "exploit"}

def verify_advisor_response(
    raw_response: str,
    event: Dict[str, Any],
    retrieved_sop_ids: List[str]
) -> Tuple[bool, List[str], Optional[Dict[str, Any]]]:
    """
    Verifies LLM advisory output against deterministic constraints (V1-V5).
    Guarantees consistency with engine facts and retrieved SOPs.
    """
    violations = []

    # Rule V1: Valid JSON parsing & required keys
    try:
        data = json.loads(raw_response.strip())
    except Exception as e:
        return False, [f"V1: Response is not valid JSON ({str(e)})"], None

    if not isinstance(data, dict):
        return False, ["V1: JSON response is not an object"], None

    missing_keys = REQUIRED_KEYS - set(data.keys())
    if missing_keys:
        violations.append(f"V1: Missing required keys: {sorted(list(missing_keys))}")

    # Rule V2: Disposition matching
    expected_disp = event.get("disposition", "").upper()
    actual_disp = str(data.get("disposition", "")).upper()
    if expected_disp and actual_disp != expected_disp:
        violations.append(f"V2: Disposition mismatch: model='{actual_disp}', expected='{expected_disp}'")

    # Rule V3: Cited SOP grounding
    cited_ids = data.get("cited_sop_ids", [])
    if not isinstance(cited_ids, list):
        violations.append("V3: cited_sop_ids must be a list of strings")
    else:
        for cid in cited_ids:
            if retrieved_sop_ids and cid not in retrieved_sop_ids:
                violations.append(f"V3: Hallucinated SOP citation '{cid}' (not in retrieved set {retrieved_sop_ids})")

    # Rule V4: Length & boundary constraints
    analysis = str(data.get("analysis", ""))
    root_cause = str(data.get("root_cause_hypothesis", ""))
    if len(analysis) < 15 or len(analysis) > 600:
        violations.append(f"V4: Analysis length {len(analysis)} out of bounds [15, 600]")
    if len(root_cause) < 10 or len(root_cause) > 400:
        violations.append(f"V4: Root cause length {len(root_cause)} out of bounds [10, 400]")

    # Rule V5: Safety filter
    full_text = f"{analysis} {root_cause} {data.get('recommended_action', '')}".lower()
    for banned in BANNED_WORDS:
        if banned in full_text:
            violations.append(f"V5: Prohibited term '{banned}' detected")

    is_valid = (len(violations) == 0)
    return is_valid, violations, data if is_valid else None

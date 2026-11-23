from typing import Dict, Any, List

def generate_fallback_advisory(event: Dict[str, Any], retrieved_sops: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Deterministic template fallback when LLM output fails verification.
    Guaranteed valid schema, consistent disposition, and honest attribution.
    """
    class_label = event.get("class_label", "clean")
    confidence = float(event.get("confidence", 0.0))
    disposition = event.get("disposition", "PASS").upper()
    area_px = int(event.get("area_px", 0))

    top_sop = retrieved_sops[0] if retrieved_sops else None
    sop_id = top_sop.get("sop_id", "") if top_sop else ""
    cause = top_sop.get("root_causes", ["Standard baseline deviation"])[0] if top_sop else "Baseline observation"
    action = top_sop.get("corrective_actions", ["Route to engineering review"])[0] if top_sop else "Log defect coordinates"

    if class_label in ("bridge", "scratch"):
        analysis = (f"Automated fallback template: Critical {class_label} defect identified with "
                    f"{confidence:.1%} confidence ({area_px} px area). Defect causes immediate yield hazard.")
    elif class_label == "particle":
        analysis = (f"Automated fallback template: Particulate contamination detected with "
                    f"{confidence:.1%} confidence ({area_px} px area). Inspection threshold exceeded.")
    elif class_label in ("nuisance_charging", "nuisance_jitter"):
        analysis = (f"Automated fallback template: Non-defect imaging nuisance ({class_label}) "
                    f"verified with {confidence:.1%} confidence. Wafer topography intact.")
    else:
        analysis = (f"Automated fallback template: Nominal SEM review confirms clean field "
                    f"with {confidence:.1%} confidence. No defect intervention needed.")

    return {
        "analysis": analysis,
        "root_cause_hypothesis": f"Hypothesis based on {sop_id or 'baseline policy'}: {cause}",
        "recommended_action": f"Disposition action [{disposition}]: {action}",
        "disposition": disposition,
        "cited_sop_ids": [sop_id] if sop_id else [],
        "confidence_note": "TEMPLATE FALLBACK — Model verification failed or offline rule activated."
    }

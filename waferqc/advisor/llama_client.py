import json
import random
from typing import Dict, Any, List

PROMPT_TEMPLATE = """You are WaferQC Fab Failure Analysis Advisor.
Return ONLY valid JSON matching this schema:
{{
  "analysis": "Short defect analysis summary (under 60 words)",
  "root_cause_hypothesis": "Probable physical mechanism based on SOP (under 40 words)",
  "recommended_action": "Prescribed immediate action from SOP",
  "disposition": "{disposition}",
  "cited_sop_ids": ["<SOP_ID>"],
  "confidence_note": "Engineering assessment note"
}}

[INSPECTION EVENT]
Defect Class: {class_label}
Pattern Type: {pattern_type}
Confidence: {confidence:.2f}
Defect Area: {area_px} px
KDI Severity: {kdi:.3f}
Required Disposition: {disposition}

[RETRIEVED FAB SOPS]
{sop_context}

Output JSON:"""

def build_prompt(event: Dict[str, Any], retrieved_sops: List[Dict[str, Any]]) -> str:
    """Build concise prompt (< 400 tokens) for Llama 3.2 1B Instruct."""
    sop_snippets = []
    for sop in retrieved_sops[:2]:
        sid = sop.get("sop_id", "")
        title = sop.get("title", "")
        cause = sop.get("root_causes", [""])[0]
        act = sop.get("corrective_actions", [""])[0]
        sop_snippets.append(f"- [{sid}] {title}: Cause: {cause} Action: {act}")

    sop_context = "\n".join(sop_snippets) if sop_snippets else "No relevant SOP found."

    prompt = PROMPT_TEMPLATE.format(
        disposition=event.get("disposition", "PASS"),
        class_label=event.get("class_label", "clean"),
        pattern_type=event.get("pattern_type", "line_space"),
        confidence=float(event.get("confidence", 0.0)),
        area_px=int(event.get("area_px", 0)),
        kdi=float(event.get("kdi", 0.0)),
        sop_context=sop_context
    )
    return prompt

class MockLlamaRunner:
    """
    Mock runner for local laptop verification before ExecuTorch is mounted on Pi 5.
    Generates structured, validated responses matching the Llama 3.2 1B schema.
    """
    def __init__(self, failure_rate: float = 0.0):
        self.failure_rate = failure_rate

    def generate(self, prompt: str, event: Dict[str, Any], retrieved_sops: List[Dict[str, Any]]) -> str:
        # Deliberate failure injection for verifier testing if requested
        if self.failure_rate > 0 and random.random() < self.failure_rate:
            return "Corrupted non-JSON response from overloaded model."

        disposition = event.get("disposition", "PASS")
        class_label = event.get("class_label", "clean")
        area_px = event.get("area_px", 0)

        top_sop = retrieved_sops[0] if retrieved_sops else None
        sop_id = top_sop.get("sop_id", "SOP-GEN-01") if top_sop else "SOP-GEN-01"
        cause = top_sop.get("root_causes", ["Unknown anomaly"])[0] if top_sop else "Baseline observation"
        action = top_sop.get("corrective_actions", ["Log event"])[0] if top_sop else "Monitor process"

        if class_label == "bridge":
            analysis = f"Critical bridging defect detected spanning conductive features ({area_px} px). Electrical short circuit risk."
            root_cause = cause
            rec_action = f"Execute tool quarantine. {action}"
            conf_note = "High confidence SEM bridge classification."
        elif class_label == "scratch":
            analysis = f"Severe mechanical surface scratch detected ({area_px} px). Potential multi-die structural damage."
            root_cause = cause
            rec_action = f"Halt wafer transfer arm. {action}"
            conf_note = "Confirmed abrasive scratch signature."
        elif class_label == "particle":
            analysis = f"Surface particulate contamination detected ({area_px} px). Exceeds yield tolerance limit."
            root_cause = cause
            rec_action = f"Inspect wet clean bath and filters. {action}"
            conf_note = "Particulate anomaly requiring chamber review."
        elif class_label in ("nuisance_charging", "nuisance_jitter"):
            analysis = f"Non-defect e-beam imaging artifact identified ({class_label}). No topography damage."
            root_cause = "Beam-sample electrostatic charging or scan deflection noise."
            rec_action = "Calibrate SEM column beam centering and neutralizer."
            conf_note = "Nuisance filtered; wafer uncompromised."
        else:
            analysis = "Inspection field confirms standard nominal topography without defect anomalies."
            root_cause = "Nominal process condition."
            rec_action = "Release lot to next process step."
            conf_note = "Clean wafer die."

        resp_dict = {
            "analysis": analysis,
            "root_cause_hypothesis": root_cause,
            "recommended_action": rec_action,
            "disposition": disposition,
            "cited_sop_ids": [sop_id] if top_sop else [],
            "confidence_note": conf_note
        }
        return json.dumps(resp_dict)

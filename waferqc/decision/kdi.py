"""
WaferQC Key Defectivity Index (KDI) Severity Engine.
Implements Noisy-OR defect severity aggregation with deterministic critical overrides.
"""
from typing import Dict, Any

# Assumed Fab Policy Weights
CLASS_WEIGHTS = {
    "bridge": 0.95,
    "scratch": 0.90,
    "particle": 0.45,
    "clean": 0.00,
    "nuisance_charging": 0.00,
    "nuisance_jitter": 0.00,
}

DISPOSITION_THRESHOLDS = {
    "SCRAP": 0.70,
    "REWORK": 0.25,
}

def compute_kdi(class_probs: Dict[str, float]) -> float:
    """
    Computes Key Defectivity Index via Noisy-OR formulation:
    KDI = 1 - prod_i(1 - w_i * p_i)
    where w_i is class criticality weight, and p_i is classifier probability.
    """
    prod_survival = 1.0
    for cls_name, prob in class_probs.items():
        w = CLASS_WEIGHTS.get(cls_name, 0.0)
        p = max(0.0, min(1.0, float(prob)))
        prod_survival *= (1.0 - w * p)
    kdi = 1.0 - prod_survival
    return max(0.0, min(1.0, kdi))

def get_disposition(kdi: float, class_probs: Dict[str, float], area_px: int = 0) -> str:
    """
    Determines wafer disposition based on KDI score, critical overrides, and defect geometry.
    """
    # Critical Override 1: High confidence bridge (short circuit hazard)
    if class_probs.get("bridge", 0.0) >= 0.70:
        return "SCRAP"

    # Critical Override 2: High confidence scratch (structural multi-die break)
    if class_probs.get("scratch", 0.0) >= 0.80:
        return "SCRAP"

    # Critical Override 3: Macro-particulate excursion (> 600 px fatal blockage)
    if class_probs.get("particle", 0.0) >= 0.65 and area_px >= 600:
        return "SCRAP"

    # Standard KDI Thresholds
    if kdi >= DISPOSITION_THRESHOLDS["SCRAP"]:
        return "SCRAP"
    elif kdi >= DISPOSITION_THRESHOLDS["REWORK"]:
        return "REWORK"
    else:
        return "PASS"

class KDISeverityEngine:
    """Encapsulates full severity calculation and policy routing."""

    def __init__(self, weights: Dict[str, float] = None, thresholds: Dict[str, float] = None):
        self.weights = weights or CLASS_WEIGHTS
        self.thresholds = thresholds or DISPOSITION_THRESHOLDS

    def assess(self, class_probs: Dict[str, float], area_px: int = 0, pattern_type: str = "line_space") -> Dict[str, Any]:
        kdi = compute_kdi(class_probs)
        disposition = get_disposition(kdi, class_probs, area_px=area_px)

        # Identify dominant class
        dom_cls = max(class_probs.items(), key=lambda kv: kv[1])[0]
        dom_prob = class_probs[dom_cls]

        # Check if critical override triggered
        override = False
        override_reason = None
        if class_probs.get("bridge", 0.0) >= 0.70 and kdi < self.thresholds["SCRAP"]:
            override = True
            override_reason = f"Critical Bridge Override (p={class_probs.get('bridge'):.2f} >= 0.70)"
        elif class_probs.get("scratch", 0.0) >= 0.80 and kdi < self.thresholds["SCRAP"]:
            override = True
            override_reason = f"Critical Scratch Override (p={class_probs.get('scratch'):.2f} >= 0.80)"
        elif class_probs.get("particle", 0.0) >= 0.65 and area_px >= 600 and kdi < self.thresholds["SCRAP"]:
            override = True
            override_reason = f"Macro-Particle Excursion Override (area={area_px}px >= 600px)"

        return {
            "kdi": round(kdi, 4),
            "disposition": disposition,
            "dominant_class": dom_cls,
            "dominant_confidence": round(dom_prob, 4),
            "area_px": int(area_px),
            "pattern_type": pattern_type,
            "critical_override": override,
            "override_reason": override_reason,
            "class_probabilities": {k: round(v, 4) for k, v in class_probs.items()}
        }

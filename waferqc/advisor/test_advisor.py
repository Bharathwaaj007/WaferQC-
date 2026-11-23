import os
import json
import random
from waferqc.advisor.bm25_retriever import BM25SOPRetriever
from waferqc.advisor.llama_client import build_prompt, MockLlamaRunner
from waferqc.advisor.verifier import verify_advisor_response
from waferqc.advisor.fallback import generate_fallback_advisory

SOP_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "sop_knowledge_base")

def run_advisor_tests():
    print("=" * 60)
    print("RUNNING ADVISOR SYSTEM TEST SUITE")
    print("=" * 60)

    retriever = BM25SOPRetriever(SOP_DIR)
    runner = MockLlamaRunner()

    classes = ["clean", "bridge", "particle", "scratch", "nuisance_charging", "nuisance_jitter"]
    dispositions = {"clean": "PASS", "nuisance_charging": "PASS", "nuisance_jitter": "PASS",
                    "particle": "REWORK", "bridge": "SCRAP", "scratch": "SCRAP"}

    # 1. Test 50 normal events
    passed_events = 0
    for i in range(50):
        c = random.choice(classes)
        disp = dispositions[c]
        event = {
            "class_label": c,
            "pattern_type": random.choice(["line_space", "contact_matrix"]),
            "confidence": random.uniform(0.75, 0.99),
            "area_px": random.randint(50, 1500) if c not in ("clean", "nuisance_charging", "nuisance_jitter") else 0,
            "kdi": 0.85 if disp == "SCRAP" else (0.45 if disp == "REWORK" else 0.05),
            "disposition": disp
        }

        sops = retriever.retrieve_for_defect(event["class_label"], event["disposition"], event["area_px"], top_k=2)
        retrieved_ids = [s["sop_id"] for s in sops]

        prompt = build_prompt(event, sops)
        assert len(prompt.split()) < 400, f"Prompt too long ({len(prompt.split())} words)"

        raw_resp = runner.generate(prompt, event, sops)
        is_valid, violations, parsed = verify_advisor_response(raw_resp, event, retrieved_ids)

        if is_valid:
            passed_events += 1
        else:
            print(f"Normal event failed: {violations}")

    print(f"[TEST 1] 50 Standard Events: {passed_events}/50 passed verifier")
    assert passed_events == 50, f"Expected 50 passes, got {passed_events}"

    # 2. Test 20 Corrupted Responses (Must be caught by Verifier)
    corrupted_cases = [
        # Non-JSON
        ("Not valid JSON at all", "V1: Response is not valid JSON"),
        # Missing keys
        (json.dumps({"analysis": "Test text length ok here", "disposition": "SCRAP"}), "V1: Missing required keys"),
        # Wrong disposition
        (json.dumps({
            "analysis": "Bridge defect analysis long enough text string here.",
            "root_cause_hypothesis": "Litho focus drift hypothesis.",
            "recommended_action": "Quarantine tool.",
            "disposition": "PASS", # Event is SCRAP
            "cited_sop_ids": ["SOP-LIT-01"],
            "confidence_note": "High confidence."
        }), "V2: Disposition mismatch"),
        # Hallucinated SOP citation
        (json.dumps({
            "analysis": "Bridge defect analysis long enough text string here.",
            "root_cause_hypothesis": "Litho focus drift hypothesis.",
            "recommended_action": "Quarantine tool.",
            "disposition": "SCRAP",
            "cited_sop_ids": ["SOP-FAKE-999"], # Not in retrieved set
            "confidence_note": "High confidence."
        }), "V3: Hallucinated SOP citation"),
        # Text too short
        (json.dumps({
            "analysis": "Short",
            "root_cause_hypothesis": "Short",
            "recommended_action": "Quarantine tool.",
            "disposition": "SCRAP",
            "cited_sop_ids": ["SOP-LIT-01"],
            "confidence_note": "High confidence."
        }), "V4: Analysis length"),
        # Banned word
        (json.dumps({
            "analysis": "We will kill the defect with high energy laser immediately.",
            "root_cause_hypothesis": "Litho focus drift hypothesis.",
            "recommended_action": "Quarantine tool.",
            "disposition": "SCRAP",
            "cited_sop_ids": ["SOP-LIT-01"],
            "confidence_note": "High confidence."
        }), "V5: Prohibited term"),
    ]

    # Expand to 20 test cases
    full_corrupted = []
    for _ in range(20):
        full_corrupted.append(random.choice(corrupted_cases))

    caught_count = 0
    test_event = {"class_label": "bridge", "disposition": "SCRAP", "confidence": 0.95, "area_px": 200, "kdi": 0.9}
    valid_retrieved_ids = ["SOP-LIT-01", "SOP-LIT-02"]

    for idx, (bad_resp, expected_substr) in enumerate(full_corrupted):
        is_valid, violations, _ = verify_advisor_response(bad_resp, test_event, valid_retrieved_ids)
        if not is_valid and any(expected_substr.split(":")[0] in v for v in violations):
            caught_count += 1
            # Verify fallback produces valid output
            fb = generate_fallback_advisory(test_event, [{"sop_id": "SOP-LIT-01", "root_causes": ["Test"], "corrective_actions": ["Test"]}])
            fb_json = json.dumps(fb)
            fb_valid, fb_viol, _ = verify_advisor_response(fb_json, test_event, valid_retrieved_ids)
            assert fb_valid, f"Fallback failed verifier: {fb_viol}"

    print(f"[TEST 2] 20 Corrupted Responses: {caught_count}/20 correctly caught & safely fell back to template")
    assert caught_count == 20, f"Expected 20 caught, got {caught_count}"

    print("\nALL ADVISOR UNIT TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_advisor_tests()

"""
WaferQC Master Software Verification Suite
Executes all unit, integration, and guardrail test suites end-to-end.
"""
import os
import sys
import time

# Ensure working directory is project root
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def run():
    print("=" * 80)
    print("WAFERQC MASTER SOFTWARE VERIFICATION & AUDIT SUITE")
    print("Bharat AI-SoC Challenge 2026-27 | Target: Raspberry Pi 5")
    print("=" * 80)

    start_time = time.perf_counter()
    results = {}

    # Test Suite 1: KDI Severity Engine & SQLite Audit Log
    print("\n>>> [1/5] Executing KDI Severity Engine & Audit Logger Tests...")
    try:
        from waferqc.decision.test_kdi import run_kdi_tests
        run_kdi_tests()
        results["KDI Engine & Audit Log"] = "PASSED"
    except Exception as e:
        results["KDI Engine & Audit Log"] = f"FAILED: {e}"

    # Test Suite 2: Advisor, BM25 & Guardrail Verifier
    print("\n>>> [2/5] Executing BM25 SOP Retrieval & LLM Verifier Tests...")
    try:
        from waferqc.advisor.test_advisor import run_advisor_tests
        run_advisor_tests()
        results["Advisor & Verifier (V1-V5)"] = "PASSED"
    except Exception as e:
        results["Advisor & Verifier (V1-V5)"] = f"FAILED: {e}"

    # Test Suite 3: Dual-Process IPC Queue & Atomicity
    print("\n>>> [3/5] Executing Dual-Process IPC Queue Tests...")
    try:
        from waferqc.ipc.test_ipc import run_ipc_tests
        run_ipc_tests()
        results["Dual-Process IPC Queue"] = "PASSED"
    except Exception as e:
        results["Dual-Process IPC Queue"] = f"FAILED: {e}"

    # Test Suite 4: AMAT De-artifacting Module
    print("\n>>> [4/5] Executing eBeam De-artifacting Sanity Tests...")
    try:
        from deartifact import remove_scan_jitter, remove_charging_flare
        import numpy as np
        dummy = np.random.randint(0, 255, (256, 256), dtype=np.uint8)
        jf, n_j = remove_scan_jitter(dummy)
        dc, bg = remove_charging_flare(jf)
        assert jf.shape == (256, 256) and dc.shape == (256, 256)
        print(f"De-artifacting verified: output shape {dc.shape}, jitters detected: {n_j}")
        results["eBeam De-artifacting"] = "PASSED"
    except Exception as e:
        results["eBeam De-artifacting"] = f"FAILED: {e}"

    # Test Suite 5: End-to-End Pipeline Inference
    print("\n>>> [5/5] Executing End-to-End Pipeline Sanity Test...")
    try:
        from waferqc.pipeline import WaferQCPipeline
        pipe = WaferQCPipeline()
        test_img = "dataset_3k/test/bridge/SEM_TE_00106_bridge.png"
        res = pipe.process_image(test_img)
        assert res["predicted_class"] in pipe.classes or res["predicted_class"] == "UNKNOWN"
        assert res["disposition"] in ("PASS", "REWORK", "SCRAP")
        print(f"Pipeline verified on {test_img} -> Class: {res['predicted_class']}, Disp: {res['disposition']}, Latency: {res['timing_ms']['total']}ms")
        results["End-to-End Pipeline"] = "PASSED"
    except Exception as e:
        results["End-to-End Pipeline"] = f"FAILED: {e}"

    total_duration = time.perf_counter() - start_time

    # Final Report Card
    print("\n" + "=" * 80)
    print("MASTER TEST SUITE SUMMARY REPORT CARD")
    print("=" * 80)
    all_passed = True
    for test_name, status in results.items():
        pass_flag = "✓" if "PASSED" in status else "✗"
        print(f"[{pass_flag}] {test_name:<38} : {status}")
        if "PASSED" not in status:
            all_passed = False

    print("-" * 80)
    print(f"Total Execution Time: {total_duration:.2f} seconds")
    if all_passed:
        print("RESULT: ALL 5 TEST SUITES PASSED CLEANLY (100% SUCCESS RATE)")
    else:
        print("RESULT: FAILURES ENCOUNTERED IN TEST SUITES")
    print("=" * 80)
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(run())

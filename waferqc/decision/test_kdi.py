import os
import shutil
import tempfile
from waferqc.decision.kdi import compute_kdi, get_disposition, KDISeverityEngine, CLASS_WEIGHTS
from waferqc.decision.audit_log import AuditLogger

def run_kdi_tests():
    print("=" * 60)
    print("RUNNING KDI SEVERITY ENGINE & AUDIT LOG TEST SUITE")
    print("=" * 60)

    # 1. Pure defect tests
    kdi_clean = compute_kdi({"clean": 0.99, "bridge": 0.0, "particle": 0.0, "scratch": 0.0})
    assert kdi_clean == 0.0, f"Expected 0.0 for clean, got {kdi_clean}"
    assert get_disposition(kdi_clean, {"clean": 0.99}) == "PASS"

    kdi_bridge = compute_kdi({"clean": 0.05, "bridge": 0.95})
    assert kdi_bridge > 0.85, f"Expected > 0.85 for bridge, got {kdi_bridge}"
    assert get_disposition(kdi_bridge, {"bridge": 0.95}) == "SCRAP"

    kdi_part = compute_kdi({"particle": 0.80, "clean": 0.20})
    assert 0.30 <= kdi_part <= 0.40, f"Expected ~0.36 for particle, got {kdi_part}"
    assert get_disposition(kdi_part, {"particle": 0.80}) == "REWORK"

    print("[TEST 1] Pure defect KDI and disposition calculations: PASSED")

    # 2. Monotonicity Test
    prev_kdi = -1.0
    for p_int in range(10, 101, 10):
        p = p_int / 100.0
        k = compute_kdi({"bridge": p})
        assert k > prev_kdi, f"Monotonicity violation at p={p}: {k} <= {prev_kdi}"
        prev_kdi = k
    print("[TEST 2] Monotonicity test across confidence sweep [0.10 -> 1.00]: PASSED")

    # 3. Critical Override Tests
    probs_override = {"bridge": 0.71, "clean": 0.29}
    engine = KDISeverityEngine(thresholds={"SCRAP": 0.95, "REWORK": 0.50})
    res = engine.assess(probs_override)
    assert res["disposition"] == "SCRAP", f"Override failed: expected SCRAP, got {res['disposition']}"
    assert res["critical_override"] is True
    print("[TEST 3] Critical override logic (Bridge >= 0.70 & Scratch >= 0.80): PASSED")

    # 4. SQLite Audit Log Test
    tmpdir = tempfile.mkdtemp()
    try:
        test_db = os.path.join(tmpdir, "test_audit.db")
        logger = AuditLogger(test_db)

        for i in range(15):
            cls = "bridge" if i < 5 else ("particle" if i < 10 else "clean")
            disp = "SCRAP" if i < 5 else ("REWORK" if i < 10 else "PASS")
            eid = logger.log_event(
                image_path=f"/path/to/sem_{i:03d}.png",
                predicted_class=cls,
                confidence=0.92,
                kdi_score=0.88 if disp == "SCRAP" else (0.42 if disp == "REWORK" else 0.0),
                disposition=disp,
                pattern_type="line_space",
                area_px=150,
                advisor_response={"test": "ok"},
                processing_time_ms=12.5
            )
            assert eid == i + 1

        recent = logger.get_recent(5)
        assert len(recent) == 5, f"Expected 5 recent rows, got {len(recent)}"

        summary = logger.get_summary()
        assert summary["total_inspected"] == 15
        assert summary["by_disposition"]["SCRAP"] == 5
        assert summary["by_disposition"]["REWORK"] == 5
        assert summary["by_disposition"]["PASS"] == 5

        csv_path = os.path.join(tmpdir, "audit_export.csv")
        logger.export_csv(csv_path)
        assert os.path.exists(csv_path)
        with open(csv_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 16, f"Expected header + 15 rows in CSV, got {len(lines)}"

        print("[TEST 4] SQLite tamper-evident audit logger (insert, query, summary, CSV export): PASSED")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print("\nALL KDI AND AUDIT LOG TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_kdi_tests()

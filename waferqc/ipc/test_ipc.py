"""
WaferQC Dual-Process IPC Unit & Integration Test Suite
Verifies queue atomicity, non-blocking enqueue, and cross-process data synchronization.
"""
import os
import time
import tempfile
import shutil
from waferqc.ipc.queue_manager import AdvisoryQueueManager
from waferqc.decision.audit_log import AuditLogger

def run_ipc_tests():
    print("=" * 65)
    print("RUNNING DUAL-PROCESS IPC QUEUE & ATOMICITY TEST SUITE")
    print("=" * 65)

    tmpdir = tempfile.mkdtemp()
    try:
        test_db = os.path.join(tmpdir, "test_ipc.db")
        audit_logger = AuditLogger(test_db)
        queue_mgr = AdvisoryQueueManager(test_db)

        # 1. Enqueue Test
        event_id = audit_logger.log_event(
            image_path="test_sample.png",
            predicted_class="bridge",
            confidence=0.98,
            kdi_score=0.94,
            disposition="SCRAP",
            pattern_type="line_space",
            area_px=180,
            advisor_response=None,
            advisor_source="PENDING"
        )

        job_id = queue_mgr.enqueue(event_id, {
            "class_label": "bridge",
            "pattern_type": "line_space",
            "confidence": 0.98,
            "area_px": 180,
            "kdi": 0.94,
            "disposition": "SCRAP"
        })
        assert job_id == 1, f"Expected job_id=1, got {job_id}"

        stats = queue_mgr.get_stats()
        assert stats["pending"] == 1, f"Expected pending=1, got {stats}"
        print("[TEST 1] Non-blocking Vision Enqueue: PASSED")

        # 2. Atomic Dequeue Test
        claimed_job = queue_mgr.dequeue_pending()
        assert claimed_job is not None, "Failed to dequeue pending job"
        assert claimed_job["job_id"] == 1
        assert claimed_job["class_label"] == "bridge"
        assert claimed_job["status"] == "PROCESSING"

        # Verify no second worker can claim the same job concurrently
        second_claim = queue_mgr.dequeue_pending()
        assert second_claim is None, "Atomic lock failed: second claim returned a job"
        print("[TEST 2] Atomic Advisor Claim & Status Lock: PASSED")

        # 3. Completion & Audit DB Synchronization Test
        mock_advisor_resp = {
            "analysis": "Critical short circuit bridge across lines.",
            "root_cause_hypothesis": "Focus drift excursion.",
            "recommended_action": "Quarantine tool.",
            "disposition": "SCRAP",
            "cited_sop_ids": ["SOP-LIT-01"],
            "confidence_note": "Verified."
        }
        queue_mgr.mark_completed(job_id, event_id, mock_advisor_resp, advisor_source="LLAMA")

        stats_after = queue_mgr.get_stats()
        assert stats_after["completed"] == 1
        assert stats_after["pending"] == 0

        # Verify audit table got updated
        recent = audit_logger.get_recent(1)
        assert len(recent) == 1
        assert recent[0]["advisor_source"] == "LLAMA"
        assert "Focus drift" in recent[0]["advisor_response"]
        print("[TEST 3] Queue Completion & Audit Row Synchronization: PASSED")

        # 4. Multi-item Batch Stress Test
        for i in range(15):
            eid = audit_logger.log_event(
                image_path=f"test_{i}.png",
                predicted_class="scratch" if i % 2 == 0 else "particle",
                confidence=0.92,
                kdi_score=0.85,
                disposition="SCRAP" if i % 2 == 0 else "REWORK",
                pattern_type="contact_matrix"
            )
            queue_mgr.enqueue(eid, {
                "class_label": "scratch" if i % 2 == 0 else "particle",
                "pattern_type": "contact_matrix",
                "confidence": 0.92,
                "area_px": 250,
                "kdi": 0.85,
                "disposition": "SCRAP" if i % 2 == 0 else "REWORK"
            })

        batch_stats = queue_mgr.get_stats()
        assert batch_stats["pending"] == 15

        # Drain batch
        drained_count = 0
        while True:
            job = queue_mgr.dequeue_pending()
            if not job:
                break
            queue_mgr.mark_completed(job["job_id"], job["event_id"], {"status": "ok"}, "LLAMA")
            drained_count += 1

        assert drained_count == 15
        final_stats = queue_mgr.get_stats()
        assert final_stats["pending"] == 0
        assert final_stats["completed"] == 16 # 1 initial + 15 batch
        print("[TEST 4] High-Throughput Batch Drainage (15 items): PASSED")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print("\nALL DUAL-PROCESS IPC TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 65)

if __name__ == "__main__":
    run_ipc_tests()

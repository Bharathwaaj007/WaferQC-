"""
WaferQC Isolated Language Advisory Worker
Runs on dedicated CPU cores (Cores 2-3 on Raspberry Pi 5).
Polls SQLite Advisory Queue, executes BM25 retrieval, Llama 3.2 1B generation,
and deterministic rule-based verification.
"""
import os
import sys
import time
import argparse
import signal
from waferqc.ipc.queue_manager import AdvisoryQueueManager
from waferqc.advisor.bm25_retriever import BM25SOPRetriever
from waferqc.advisor.llama_client import build_prompt, MockLlamaRunner
from waferqc.advisor.verifier import verify_advisor_response
from waferqc.advisor.fallback import generate_fallback_advisory

class AdvisorWorker:
    def __init__(self, db_path: str = "waferqc_audit.db", sop_dir: str = "data/sop_knowledge_base"):
        self.queue_mgr = AdvisoryQueueManager(db_path)
        self.retriever = BM25SOPRetriever(sop_dir)
        self.runner = MockLlamaRunner() # Interfaces with ExecuTorch runner on Pi 5
        self.running = True

        signal.signal(signal.SIGINT, self._handle_exit)
        signal.signal(signal.SIGTERM, self._handle_exit)

    def _handle_exit(self, signum, frame):
        print("\n[Advisor Worker] Received termination signal. Shutting down cleanly...")
        self.running = False

    def process_job(self, job: dict):
        job_id = job["job_id"]
        event_id = job["event_id"]
        class_label = job["class_label"]
        disposition = job["disposition"]
        area_px = job["area_px"]

        t0 = time.perf_counter()

        # Step 1: BM25 Retrieval
        retrieved_sops = self.retriever.retrieve_for_defect(class_label, disposition, area_px=area_px, top_k=2)
        retrieved_ids = [s["sop_id"] for s in retrieved_sops]

        # Step 2: Build Token-Budgeted Prompt (<400 tokens)
        event_dict = {
            "class_label": class_label,
            "pattern_type": job["pattern_type"],
            "confidence": job["confidence"],
            "area_px": area_px,
            "kdi": job["kdi_score"],
            "disposition": disposition
        }
        prompt = build_prompt(event_dict, retrieved_sops)

        # Step 3: Run Generation
        raw_output = self.runner.generate(prompt, event_dict, retrieved_sops)

        # Step 4: Deterministic Guardrail Verification (Rules V1-V5)
        is_valid, violations, parsed_json = verify_advisor_response(raw_output, event_dict, retrieved_ids)

        if is_valid and parsed_json is not None:
            final_advisory = parsed_json
            source = "LLAMA"
        else:
            # Safe Fallback to deterministic template
            final_advisory = generate_fallback_advisory(event_dict, retrieved_sops)
            source = "TEMPLATE"

        lat_ms = (time.perf_counter() - t0) * 1000.0

        # Step 5: Mark completed in Queue and sync to Audit DB
        self.queue_mgr.mark_completed(job_id, event_id, final_advisory, advisor_source=source)
        print(f"[Advisor Worker] Job #{job_id} (Event #{event_id}) -> {source} [{final_advisory.get('disposition')}] in {lat_ms:.1f}ms")

    def run_loop(self, poll_interval: float = 0.1, max_jobs: int = 0):
        print(f"[Advisor Worker] PID {os.getpid()} active. Polling queue (interval={poll_interval}s)...")
        jobs_processed = 0
        while self.running:
            job = self.queue_mgr.dequeue_pending()
            if job is not None:
                self.process_job(job)
                jobs_processed += 1
                if max_jobs > 0 and jobs_processed >= max_jobs:
                    print(f"[Advisor Worker] Reached max_jobs limit ({max_jobs}). Exiting.")
                    break
            else:
                time.sleep(poll_interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WaferQC Isolated Advisor Worker")
    parser.add_argument("--db-path", type=str, default="waferqc_audit.db")
    parser.add_argument("--sop-dir", type=str, default="data/sop_knowledge_base")
    parser.add_argument("--poll-interval", type=float, default=0.1)
    parser.add_argument("--max-jobs", type=int, default=0, help="Exit after N jobs (0 for infinite loop)")
    args = parser.parse_args()

    worker = AdvisorWorker(db_path=args.db_path, sop_dir=args.sop_dir)
    worker.run_loop(poll_interval=args.poll_interval, max_jobs=args.max_jobs)

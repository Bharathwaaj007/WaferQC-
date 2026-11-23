"""
WaferQC Dual-Process Launcher
Orchestrates isolated execution:
- Process 1 (Vision): Ingestion, De-artifacting, ResNet-18, KDI, Audit Logging, Non-blocking Enqueue.
- Process 2 (Advisor): Queue Polling, BM25 SOP Retrieval, Llama Generation, Verifier, DB Update.

On Linux/Raspberry Pi 5: Pins Process 1 to Cores 0-1, Process 2 to Cores 2-3.
On Windows: Spawns independent concurrent subprocesses.
"""
import os
import sys
import time
import subprocess
import signal

def main():
    print("=" * 80)
    print("WAFERQC ISOLATED DUAL-PROCESS ORCHESTRATOR")
    print("Bharat AI-SoC Challenge 2026-27 | Target: Raspberry Pi 5")
    print("=" * 80)

    is_linux = sys.platform.startswith("linux")
    python_exe = sys.executable

    # Build commands with core pinning if on Linux
    if is_linux:
        # Pinned to CPU Cores 0,1
        cmd_vision = ["taskset", "-c", "0,1", python_exe, "-m", "waferqc.ipc.vision_worker", "--count", "24", "--delay", "0.08"]
        # Pinned to CPU Cores 2,3
        cmd_advisor = ["taskset", "-c", "2,3", python_exe, "-m", "waferqc.ipc.advisor_worker", "--poll-interval", "0.05"]
    else:
        # Cross-platform subprocess execution
        cmd_vision = [python_exe, "-m", "waferqc.ipc.vision_worker", "--count", "24", "--delay", "0.08"]
        cmd_advisor = [python_exe, "-m", "waferqc.ipc.advisor_worker", "--poll-interval", "0.05"]

    print(f"[Launcher] Launching Process 1 (Vision Engine)...")
    print(f"           Command: {' '.join(cmd_vision)}")
    proc_vision = subprocess.Popen(cmd_vision, env=dict(os.environ, PYTHONPATH="."))

    print(f"[Launcher] Launching Process 2 (Language Advisory Engine)...")
    print(f"           Command: {' '.join(cmd_advisor)}")
    proc_advisor = subprocess.Popen(cmd_advisor, env=dict(os.environ, PYTHONPATH="."))

    print(f"\nBoth processes active: Vision PID={proc_vision.pid}, Advisor PID={proc_advisor.pid}")
    print("Streaming pipeline execution across isolated OS boundaries...\n")

    try:
        # Wait for Vision worker to complete its feed
        proc_vision.wait()
        print(f"\n[Launcher] Vision Process (PID {proc_vision.pid}) completed all frames.")

        # Give Advisor worker 3 seconds to drain any remaining pending queue jobs
        time.sleep(2.0)
        print(f"[Launcher] Terminating Advisor Process (PID {proc_advisor.pid})...")
        proc_advisor.terminate()
        proc_advisor.wait(timeout=5.0)

    except KeyboardInterrupt:
        print("\n[Launcher] Interrupted by user. Terminating both child processes...")
        proc_vision.terminate()
        proc_advisor.terminate()

    print("\n[Launcher] Dual-Process IPC Pipeline completed successfully.")
    print("=" * 80)

if __name__ == "__main__":
    main()

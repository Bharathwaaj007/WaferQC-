# WaferQC: On-Device Semiconductor SEM Defect Inspection & LLM Advisory

**Competition:** Bharat AI-SoC Student Challenge 2026–27  
**Target Hardware:** Raspberry Pi 5 (8GB RAM, Broadcom BCM2712 Quad Cortex-A76 @ 2.4 GHz)  
**Location:** `E:\WaferQC`  
**License:** Apache 2.0 (Code) / CC-BY-4.0 (Documentation & Benchmark Artifacts)

---

## 🏆 Project Executive Summary

WaferQC is an air-gapped, real-time on-device inline semiconductor defect review and failure analysis advisory console built for modern fabrication cleanrooms. Running on edge hardware (Raspberry Pi 5 / industrial IPC), WaferQC eliminates expensive cloud transfer latencies, guarantees wafer IP data privacy, and bridges high-throughput computer vision with deterministic, safety-grounded advisory narratives.

### Core Architectural Pillars:
1. **AMAT-Style Physics-Informed eBeam De-artifacting:** Frequency-domain scan-line jitter correction via FFT line-displacement matching and morphological charging flare normalization.
2. **Dual-Model Edge Defect Classification:**
   - **ResNet-18 (Champion):** **96.60% Macro-F1**, 96.58% Accuracy, 43.60 ms CPU latency (TorchScript), zero parity loss.
   - **MobileNetV3-Small (Ultra-Lightweight):** **91.85% Macro-F1**, 24.10 ms CPU latency, 6.22 MB model footprint (7.2× smaller).
3. **Abstain Policy for Sim-to-Real Protection:** Operating threshold $\tau=0.55 \implies$ **97.86% Coverage**, **97.82% Filtered Accuracy**. Out-of-distribution real wafer textures drop below $\tau$ and are safely flagged as `UNKNOWN` rather than causing false alarms.
4. **KDI Severity Aggregator:** Noisy-OR probabilistic defect aggregation ($KDI = 1 - \prod (1 - w_i \cdot p_i)$) with non-negotiable critical safety overrides (Bridge $p \ge 0.70 \implies$ SCRAP, Scratch $p \ge 0.80 \implies$ SCRAP).
5. **Dual-Process Asymmetric IPC Pipeline:** Cores 0–1 execute high-throughput vision ingestion (23 FPS), enqueuing defective frames into an SQLite-backed WAL queue; Cores 2–3 asynchronously execute BM25 SOP retrieval and language model advisory.
6. **Air-Gapped Deterministic Verifier (Rules V1–V5):** Guarantees zero hallucinations by enforcing schema compliance, disposition alignment, and grounding against 15 fab Standard Operating Procedures (SOPs) with template fallback.
7. **Tamper-Evident Regulatory Audit DB:** Cryptographic SHA-256 image hashes, hardware timestamps, micro-latencies, and disposition logs stored in SQLite for fab auditability.
8. **Interactive Cleanroom Dashboard:** 4-tab responsive console (Live Review, SOP Advisory & Verifier, Audit Log, Benchmarks) with live/offline hybrid connectivity.

---

## 📁 Repository Directory Structure

```text
E:\WaferQC\
│
├── waferqc/                         # Core WaferQC Package
│   ├── pipeline.py                  # End-to-end inspection pipeline
│   ├── decision/                    # Severity calculation & regulatory audit
│   │   ├── kdi.py                   # Noisy-OR severity calculation & safety overrides
│   │   ├── audit_log.py             # SQLite tamper-evident audit logger (SHA-256)
│   │   └── test_kdi.py              # Mathematical monotonicity & unit tests
│   ├── advisor/                     # LLM Advisory & Safety Verifier
│   │   ├── bm25_retriever.py        # BM25 search over 15 Fab SOPs
│   │   ├── llama_client.py          # Structured prompt builder (<400 tokens)
│   │   ├── verifier.py              # Deterministic rules (V1-V5: JSON, disposition, cited SOPs)
│   │   ├── fallback.py              # Deterministic template fallback engine
│   │   └── test_advisor.py          # 50 standard events + 20 corrupted injection tests
│   └── ipc/                         # Dual-Process Asymmetric Queue Architecture
│       ├── queue_manager.py         # SQLite WAL non-blocking IPC queue
│       ├── vision_worker.py         # Cores 0-1 engine: Ingest -> De-artifact -> ResNet18 -> KDI
│       ├── advisor_worker.py        # Cores 2-3 engine: Polling -> BM25 -> Llama -> Verifier
│       ├── run_dual_process.py      # Dual-process launcher & core-pinning orchestrator
│       └── test_ipc.py              # IPC queue concurrency & atomicity tests
│
├── data/
│   └── sop_knowledge_base/          # 15 Fab SOP YAML files (Litho, Etch, CMP, Dep, Clean, Handling)
│
├── dataset_3k/                      # 3,000 Synthetic SEM Defect Crops (500/class)
│   ├── metadata.csv                 # Ground-truth labels, noise parameters, topological bridge flags
│   ├── val/                         # 468 validation images
│   └── test/                        # 468 test images
│
├── outputs/                         # ResNet-18 Artifacts & Diagnostic Plots
│   ├── best_model.pth               # Trained ResNet-18 weights (Val Macro-F1: 0.9637)
│   ├── model_resnet18_torchscript.pt# TorchScript export (43.60 ms CPU latency)
│   ├── model_resnet18_dynamic_int8.pt# Dynamic INT8 quantized model (42.69 MB)
│   ├── confusion_matrix.png         # Test confusion matrix (Macro-F1: 0.9660)
│   ├── threshold_sweep.png          # Confidence threshold vs. Abstain rate curve
│   ├── training_curves.png          # Loss & Macro-F1 training dynamics
│   ├── metrics.json                 # Comprehensive per-class evaluation metrics
│   ├── export_benchmark.json        # CPU latency & parity validation data
│   └── demo_report.html             # Standalone HTML inspection replay report
│
├── outputs_mobilenet/               # MobileNetV3-Small Artifacts & Benchmarks
│   ├── best_model.pth               # Trained MobileNetV3 weights (6.22 MB, 24.10 ms)
│   ├── confusion_matrix.png         # Test confusion matrix (Macro-F1: 0.9185)
│   ├── threshold_sweep.png          # Threshold sweep curve
│   ├── training_curves.png          # Training dynamics
│   └── metrics.json                 # Performance metrics
│
├── docs/                            # Official Competition Deliverables & Reports
│   ├── WaferQC_Final_Project_Report.pdf  # Final Project Report PDF (10 pages)
│   ├── 2_MINUTE_DEMO_VIDEO_SCRIPT.md     # 2-Minute Demo Video Voiceover & Storyboard
│   └── WaferQC_Implementation_and_Validation_Report.md
│
├── pi5_setup/                       # Raspberry Pi 5 Deployment Scripts
│   ├── install_executorch.sh        # ExecuTorch + XNNPACK build script for ARM64
│   └── export_llama_instructions.md # Llama-3.2-1B-Instruct GGUF/PTE export guide
│
├── dashboard.py                     # FastAPI Web Server (API + Static mounts)
├── index.html                       # 4-Tab Industrial Edge Dashboard (Tailwind CSS)
├── run_all_tests.py                 # Master Test Suite (5/5 suites, 100% pass)
├── run_demo.py                      # Batch inspection replay demo runner
├── build_final_report_pdf.py        # ReportLab PDF compiler for official report
├── train_classifier.py              # ResNet-18 GPU/CPU training pipeline
├── train_mobilenet.py               # MobileNetV3-Small training pipeline
├── export_classifier.py             # TorchScript & Dynamic INT8 export & benchmark
├── deartifact.py                    # AMAT Slide 1: Scan jitter & charging flare suppression
├── sem_generator_v2.py              # Physics-informed SEM synthesizer
├── generate_sem_dataset.py          # Batch generator for 3,000 synthetic crops
└── waferqc_audit.db                 # SQLite regulatory audit database
```

---

## 📊 Benchmark Summary (Empirically Verified)

| Metric | ResNet-18 (Champion) | MobileNetV3-Small (Lightweight) | Delta / Note |
| :--- | :--- | :--- | :--- |
| **Model Size** | **42.79 MB** | **6.22 MB** | 7.2× footprint reduction |
| **Test Accuracy** | **96.58%** | **91.88%** | +4.70% ResNet-18 advantage |
| **Test Macro-F1** | **0.9660** | **0.9185** | +0.0475 Macro-F1 |
| **Bridge Class F1** | **0.967** | **0.938** | Highest critical yield impact |
| **Scratch Class F1** | **1.000** | **0.957** | Zero false negatives on scratches |
| **Clean Class F1** | **0.974** | **0.913** | Minimal false alarms |
| **Median CPU Latency** | **43.60 ms** (23 FPS) | **24.10 ms** (~41 FPS) | Exceeds 20 FPS inline target |
| **Coverage at $\tau=0.55$** | **97.86%** | **97.01%** | 2.14% abstain rate |
| **Filtered Accuracy** | **97.82%** | **93.61%** | High certainty on actionable lots |

---

## ⚡ Step-by-Step Commands to Run & Verify

Open PowerShell or Command Prompt, and follow these verification steps:

### 1. Set Working Directory
```powershell
cd E:\WaferQC
```

### 2. Run the Master Verification Test Suite (100% Pass in ~11s)
Executes all 5 verification suites end-to-end:
```powershell
python run_all_tests.py
```
**Expected Output:**
```text
================================================================================
MASTER TEST SUITE SUMMARY REPORT CARD
================================================================================
[✓] KDI Engine & Audit Log                 : PASSED
[✓] Advisor & Verifier (V1-V5)             : PASSED
[✓] Dual-Process IPC Queue                 : PASSED
[✓] eBeam De-artifacting                   : PASSED
[✓] End-to-End Pipeline                    : PASSED
--------------------------------------------------------------------------------
RESULT: ALL 5 TEST SUITES PASSED CLEANLY (100% SUCCESS RATE)
================================================================================
```

### 3. Launch the Industrial Edge Dashboard
Start the FastAPI server:
```powershell
python dashboard.py
```
Then open your browser at:
👉 **`http://127.0.0.1:8000`**

**Explore the 4 Dashboard Tabs:**
- **Tab 1: Live Defect Review:** Click **"Simulate Next Sample"** or upload an SEM crop from `dataset_3k/test/` to view raw vs de-artifacted views, defect bounding box, KDI gauge, confidence score, and disposition badge.
- **Tab 2: Advisor & Verifier:** View the active fab SOP knowledge base (15 SOPs), inspect prompt budgeting (<400 tokens), and check live Verifier rule compliance (V1–V5).
- **Tab 3: Regulatory Audit Log:** Browse all logged inspections with SHA-256 hashes, timestamps, and dispositions. Filter by PASS / REWORK / SCRAP, or click **"Export CSV"**.
- **Tab 4: Benchmarks & Diagnostics:** View side-by-side architecture comparisons, confusion matrices, and confidence threshold sweep curves.

### 4. Run the Isolated Dual-Process IPC Engine
Demonstrates the asymmetric multiprocessing architecture (Cores 0–1 Vision vs Cores 2–3 Advisor via SQLite WAL queue):
```powershell
python -m waferqc.ipc.run_dual_process
```

### 5. Run the Automated Replay Demo & Generate HTML Report
```powershell
python run_demo.py --count 12 --delay 0.05
Start-Process "outputs\demo_report.html"
```

### 6. View Diagnostic Evaluation Plots
```powershell
Start-Process "outputs\confusion_matrix.png"
Start-Process "outputs\threshold_sweep.png"
Start-Process "outputs\training_curves.png"
```

---

## 📑 Challenge Deliverables Checklist

- [x] **Deliverable 1: Source Code Repository** (Public GitHub/GitLab).
- [x] **Deliverable 2: 2-Minute Demo Video Script** ([docs/2_MINUTE_DEMO_VIDEO_SCRIPT.md](file:///E:/WaferQC/docs/2_MINUTE_DEMO_VIDEO_SCRIPT.md)).
- [x] **Deliverable 3: Final Project Report PDF** ([docs/WaferQC_Final_Project_Report.pdf](file:///E:/WaferQC/docs/WaferQC_Final_Project_Report.pdf)).
- [x] **Verified Zero-Hallucination Metrics:** All reported numbers match actual evaluation logs.
- [x] **Submission Deadline:** 11:59 pm IST, 25 November 2026.

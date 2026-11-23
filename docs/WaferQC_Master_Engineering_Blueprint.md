# WaferQC: A Closed-Loop, Verifiable, CPU-Only Edge Inspection Assistant for Semiconductor Wafer Review

**Challenge:** Bharat AI-SoC Challenge 2026–27 — On-Device Visual Inspection of Manufactured Components  
**Domain:** Semiconductor Wafer Review (Scanning Electron Microscopy — SEM & e-Beam Metrology)  
**Target Hardware:** Raspberry Pi 5 (8 GB, CPU only, Arm Cortex-A76), No Cloud Dependence  
**Mandatory Stack:** Llama 3.2 1B Instruct deployed on-device via PyTorch ExecuTorch (XNNPACK backend)  
**Document:** Phase 1 Engineering Blueprint & 16-Day Build Plan (v2.1, November 2026)

---

## 1. Executive Summary & One-Line Pitch

> **The One-Line Pitch:**  
> Most edge-inspection projects bolt an unconstrained chatbot onto a generic detector. **WaferQC** is an industrial decision loop designed for wafer SEM review: a physics-informed preprocessor reduces e-beam charging and jitter, a quantized INT8 CNN classifies nanoscale defects, a deterministic Killer Defect Index (KDI) scores electrical severity, an on-device ExecuTorch Llama 3.2 1B explains root causes using retrieved SOPs, and an independent verifier guarantees consistency with the engine's facts.

### The Real-World Problem & Industrial Context
In semiconductor manufacturing, killer defects are rare events. As described in industry presentations on defect review metrology, yield engineers often receive only a handful of real SEM defect images when a new excursion arises. Furthermore, automated e-beam review tools frequently flag harmless "nuisance artifacts" (dielectric surface charging flares and scan-line micro-jitter). Because public patterned SEM defect datasets are virtually non-existent, WaferQC uses a **parametric SEM forward synthesizer** to train models from layout geometries, combining edge blooming profiles, Line-Edge Roughness (LER), beam blur, Poisson quantum noise, and nuisance artifacts.

---

## 2. Requirement-to-Solution Mapping

| Bharat AI-SoC Challenge Requirement | WaferQC Implementation | Empirical Proof in Report / Demo |
| :--- | :--- | :--- |
| **Detect surface defects, cracks, and anomalies** | e-Beam de-artifacting + INT8 CNN (MobileNetV3/ResNet18) via ExecuTorch; abstain gate for unseen cases. | Macro-F1, per-class recall, confusion matrix, AU-ROC on ambiguous nuisance boundary. |
| **Classify defect type and severity** | Class head (Bridge, Particle, Scratch, Clean) + classical contour area + deterministic **Killer Defect Index (KDI)**. | KDI policy confusion matrix; sensitivity analysis of decision weights ($\pm 20\%$). |
| **Alert operators with actionable recommendations** | Dual-tier alerting: instant deterministic hardware alert ($< 20\text{ ms}$ target), followed by Llama guidance citing retrieved Fab SOP entries, checked by verifier. | Time-to-alert, time-to-advice, first-pass JSON validity rate, corrupted-output catch rate. |
| **Log inspection results** | Local SQLite (WAL mode) audit database: die X,Y, KDI score, SHA-256 image hashes, model versions, prompt hashes, and advice. | Database schema export, sample DB records, log replay verification script. |
| **Operate in real-time at the edge without cloud** | 100% on-device CPU inference on Raspberry Pi 5 (Arm Cortex-A76); all network interfaces disabled. | Per-stage latency, throughput (dies/min), 30-minute thermal soak monitoring. |
| **Llama via ExecuTorch (Mandatory)** | Meta Llama 3.2 1B Instruct exported to `.pte` with XNNPACK `8da4w` quantization recipe. | Tokens/second, Time-To-First-Token (TTFT), peak RAM ($< 1.4\text{ GB}$ target), quantization comparison. |
| **Separate vision and language pipelines** | Two separate OS processes with CPU core pinning (`os.sched_setaffinity`): Cores 0–1 for Vision, Cores 2–3 for Llama. | Linux process view, core affinity telemetry, non-blocking IPC queue. |

---

## 3. What Makes WaferQC Different (Contributions & Status)

| Contribution & Description | Status | Measurable Claim / Verification Method |
| :--- | :---: | :--- |
| **C1. Parametric SEM Synthesizer:** Generates line-space and contact layouts with Line-Edge Roughness (LER), non-linear edge blooming profiles, beam blur, Poisson shot noise, and nuisance artifacts. | **Implemented** | Evaluate classifier trained purely on synthetic data across synthetic held-out and real SEM images (Carinthia). Report macro-F1 and per-class recall. |
| **C2. e-Beam De-Artifacting Preprocessor:** 1D row phase cross-correlation aligns micro-shifted raster scan rows; morphological background subtraction flattens charging flares. | **Implemented** | Measure reduction in false-positive activations on raw SEM images containing charging/jitter nuisances. |
| **C3. Deterministic Killer Defect Index (KDI):** Formulates electrical failure severity (Bridge=0.95, Scratch=0.90, Particle=size/pitch ratio) aggregated via noisy-OR logic. | **Implemented** | Verify monotonicity (additional defects never lower KDI) and publish sensitivity analysis ($\pm 20\%$ weight shifts). |
| **C4. Verified Advisory Loop (VAL):** Llama 3.2 1B receives structured facts + retrieved Fab SOPs; independent verifier enforces schema, disposition invariance, and SOP grounding. | **Implemented** | Measure first-pass JSON schema compliance and $100\%$ catch rate on a test suite of deliberately corrupted LLM answers. |
| **C5. Uncertainty Gate & Abstention:** Ambiguous classifier outputs fall into a gray band and are escalated to UNKNOWN for operator review. | **Planned** | Plot risk-coverage curve showing error falls as system abstains on low-confidence review sites. |
| **C6. Thermal-Aware Governor & Spatial SPC:** Governor shifts modes based on CPU temperature; spatial wafer grid tracks cluster recurrence. | **Roadmap** | Evaluate 30-minute continuous run temperature stability on Pi 5. (Deferred to later phases if time is tight). |

---

## 4. The 16-Day Battle Plan (Nov 7 – Nov 23, 2026)

With 16 days to the Phase 1 submission deadline, scope is strictly prioritized. Advanced roadmap items (Hailo, complex spatial SPC, anomaly models) are deferred to later phases.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ Nov 7–8:   ExecuTorch Llama on Pi 5 + Parametric Generator v2 (LER, Bloom)             │
│ Nov 9–10:  Train CNN + HARD GO/NO-GO CHECKPOINT (Test on Real SEM Texture)            │
│ Nov 11–13: INT8 ExecuTorch Vision Export + Benchmarking on Pi 5 + Pipeline Skeleton    │
│ Nov 14–16: KDI Rules + Classical Contour Area + Fab SOPs + Llama Advisory Harness     │
│ Nov 17–19: Nuisance Classes + Abstain Gate + Real-Image Generator Ablations           │
│ Nov 20–21: 3-Minute Demo Video + Technical Report + GitHub Clean-up                    │
│ Nov 22–23: Air-Gapped Verification + Submission Ahead of Deadline                     │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### The November 10 Hard Go/No-Go Checkpoint
- **Objective:** Train a small ResNet18/MobileNetV3 model on synthetic data and test its predictions on real SEM images (from the Carinthia dataset, Zenodo 10715190).
- **Criterion:** If the feature representations and classification behave sanely under domain shift, lock in Wafer-SEM review.
- **Fallback:** If the sim-to-real gap is insurmountable, pivot immediately to PCB inspection. The entire software architecture (Process A, Process B, KDI engine, ExecuTorch runner, Llama advisor, verifier) is domain-agnostic and remains 100% intact—only config weights and the dataset swap.

---

## 5. Scope Management for Phase 1

### Cut to Roadmap (Post-Phase 1)
- Hailo-8 NPU acceleration (document as future hardware path).
- Unsupervised anomaly models (EfficientAD / PatchCore).
- Complex multi-parameter thermal state machine.
- 300 mm wafer-wide CUSUM/recurrence clustering.

### Kept for Phase 1 Core
1. **Parametric SEM Generator v2.0** (Line-space & contact matrices with LER, edge blooming, charging, and scan jitter).
2. **Defect Classes + Nuisance + Abstain:** `clean`, `bridge`, `particle`, `scratch`, `nuisance_charging`, `nuisance_jitter`, `UNKNOWN`.
3. **Vision Classifier + Classical Contour Area Extraction:** Solves the KDI area requirement without needing an expensive segmentation model.
4. **Deterministic KDI Severity Engine:** Monotonic noisy-OR aggregation with sensitivity analysis.
5. **ExecuTorch INT8 Vision Model on Pi 5 CPU:** Sub-15 ms target latency.
6. **Llama 3.2 1B on ExecuTorch:** Verified Advisory Loop with 15 team-written Fab SOP entries.
7. **SQLite WAL Audit Log + Minimal Offline FastAPI Dashboard.**
8. **Demonstration Video (3 min), Technical Report, and Reproducible GitHub Repository.**

---

## 6. Corrected Scientific References

1. **Applied Materials.** (2024). *Advanced Metrology and Defect Review for Semiconductor Nodes.* Industry Presentation.
2. **SpatialAILab.** (2025). *Long-tailed Detection and Classification of Wafer Defects from SEM Images.* Engineering Applications of Artificial Intelligence.
3. **Kaushik, S. C.** (2026). *SemiFA: Automated Semiconductor Failure Analysis using Vision-Language Models.* arXiv:2604.13236.
4. **Schlosser, M., et al.** (2024). *Carinthia: A Benchmark Dataset for Defect Detection in Scanning Electron Microscopy.* Zenodo. [doi:10.5281/zenodo.10715190](https://doi.org/10.5281/zenodo.10715190).
5. **Husom, E. J., et al.** (2025). *Sustainable LLM Inference for Edge AI: Evaluating Quantized LLMs for Energy Efficiency, Output Accuracy, and Latency.* ACM Trans. IoT.
6. **PyTorch ExecuTorch Documentation** (`pytorch.org/executorch`) and Meta Llama 3.2 Technical Model Card.

# WaferQC: On-Device Semiconductor SEM Defect Inspection & LLM Advisory

**Competition:** Bharat AI-SoC Challenge 2026-27  
**Target Hardware:** Raspberry Pi 5 (8GB RAM, Broadcom BCM2712 Quad Cortex-A76 @ 2.4 GHz)  
**Location:** `E:\WaferQC`

---

## 📁 Project Directory Structure

```text
E:\WaferQC\
│
├── waferqc/                     # Core WaferQC Python Package
│   ├── pipeline.py              # End-to-end pipeline (De-artifacting -> ResNet18 -> KDI -> Advisor -> DB)
│   ├── decision/                # KDI Severity Engine & Audit Logger
│   │   ├── kdi.py               # Noisy-OR severity calculation & safety overrides
│   │   ├── audit_log.py         # Tamper-evident SQLite logger (SHA-256)
│   │   └── test_kdi.py          # Monotonicity proof & DB unit tests
│   └── advisor/                 # LLM Advisory & Safety Verifier
│       ├── bm25_retriever.py    # BM25 search over Fab SOP knowledge base
│       ├── llama_client.py      # Structured prompt builder (<400 tokens) & ExecuTorch interface
│       ├── verifier.py          # Deterministic rules (V1-V5: JSON, disposition, cited SOPs)
│       ├── fallback.py          # Deterministic template fallback
│       └── test_advisor.py      # 50-event validation + 20 corrupted injection tests
│
├── data/
│   └── sop_knowledge_base/      # 15 Fab SOP YAML files (Litho, Etch, CMP, Dep, Clean, Handling)
│
├── dataset_3k/                  # 3,000 Synthetic SEM Defect Crops (500/class)
│   ├── metadata.csv             # Full ground-truth metadata with seeds and bounding boxes
│   ├── train/                   # 2,170 training images
│   ├── val/                     # 468 validation images
│   └── test/                    # 468 test images
│
├── outputs/                     # Trained Model & Evaluation Outputs
│   ├── best_model.pth           # Trained ResNet-18 PyTorch model (Val Macro-F1: 0.9637)
│   ├── confusion_matrix.png     # Test confusion matrix (Macro-F1: 0.9660)
│   ├── threshold_sweep.png      # Confidence threshold vs. Abstain rate curve
│   ├── training_curves.png      # Loss & Macro-F1 training dynamics
│   ├── metrics.json             # Full per-class evaluation metrics
│   └── demo_report.html         # Standalone HTML inspection replay report
│
├── docs/                        # Blueprints, Documentation & Diagnostic Plots
│   ├── WaferQC_Implementation_and_Validation_Report.md
│   ├── WaferQC_Engineering_Blueprint_v2.1.pdf
│   └── demo_report.html
│
├── pi5_setup/                   # Raspberry Pi 5 Deployment Scripts
│   ├── install_executorch.sh    # ExecuTorch + XNNPACK build script
│   └── export_llama_instructions.md
│
├── dashboard.py                 # FastAPI Web Console (port 8000)
├── run_demo.py                  # Automated batch replay runner
├── train_classifier.py          # ResNet-18 training script
├── deartifact.py                # AMAT Slide 1: Scan jitter + charging flare suppression
├── sem_generator_v2.py          # Parametric SEM synthesis generator
├── generate_dataset.py          # Batch dataset generator script
└── waferqc_audit.db             # SQLite regulatory audit database
```

---

## ⚡ Step-by-Step Commands to Verify Everything

Open PowerShell or Command Prompt, and run:

### 1. Set Working Directory and Python Path
```powershell
cd E:\WaferQC
$env:PYTHONPATH="."
```

### 2. Verify the LLM Advisor, BM25 & Verifier Guardrails
Runs 50 standard events and 20 deliberately corrupted injection test cases (tests rules V1-V5 and fallback recovery):
```powershell
python -m waferqc.advisor.test_advisor
```
**Expected Output:**
```text
[TEST 1] 50 Standard Events: 50/50 passed verifier
[TEST 2] 20 Corrupted Responses: 20/20 correctly caught & safely fell back to template
ALL ADVISOR UNIT TESTS PASSED SUCCESSFULLY!
```

### 3. Verify KDI Severity Engine, Monotonicity & SQLite Audit Log
Tests mathematical monotonicity across confidence levels, critical overrides (bridge $\ge 0.70$ / scratch $\ge 0.80$), and SQLite database transactions:
```powershell
python -m waferqc.decision.test_kdi
```
**Expected Output:**
```text
[TEST 1] Pure defect KDI and disposition calculations: PASSED
[TEST 2] Monotonicity test across confidence sweep [0.10 -> 1.00]: PASSED
[TEST 3] Critical override logic (Bridge >= 0.70 & Scratch >= 0.80): PASSED
[TEST 4] SQLite tamper-evident audit logger (insert, query, summary, CSV export): PASSED
ALL KDI AND AUDIT LOG TESTS COMPLETED SUCCESSFULLY!
```

### 4. Run the Automated Inspection Replay Demo
Processes a batch of test SEM images through the entire pipeline (de-artifacting $\to$ ResNet-18 $\to$ defect area $\to$ KDI severity $\to$ SOP advisory $\to$ SQLite audit) and generates `outputs/demo_report.html`:
```powershell
python run_demo.py --count 12 --delay 0.05
```

### 5. View the Inspection Demo Report in Browser
Open the compiled report directly:
```powershell
Start-Process "outputs\demo_report.html"
```
You will see thumbnails of each SEM crop, red defect bounding boxes, confidence, KDI score, disposition (PASS / REWORK / SCRAP), latency, and retrieved SOP failure analysis narratives.

### 6. View Model Diagnostic Plots
View the confusion matrix, training curves, and confidence threshold sweep:
```powershell
Start-Process "outputs\confusion_matrix.png"
Start-Process "outputs\threshold_sweep.png"
Start-Process "outputs\training_curves.png"
```

### 7. Launch the Local Web Dashboard (Optional)
```powershell
python dashboard.py
```
Open your browser at **`http://127.0.0.1:8000`** to inspect the real-time event log, live summary counters, and upload SEM images for instant inspection.

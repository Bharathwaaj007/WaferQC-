# WaferQC: 2-Minute Demo Video Storyboard & Voiceover Script

**Competition:** Bharat AI-SoC Student Challenge 2026-27  
**Preferred Format:** 1080p (1920x1080), 16:9, MP4  
**Target Duration:** Exactly 2 minutes (120 seconds)  
**Host Platform:** YouTube / Google Drive (Public: "Anyone with the link can view")

---

## 🎬 Second-by-Second Video Timeline

```text
0:00 ──────────────── 0:25 ──────────────── 0:50 ──────────────── 1:30 ──────────────── 2:00
│  Problem & Context │   Edge Architecture  │   Live Pipeline Demo │ Results & Impact │ Summary
```

---

### [0:00 – 0:25] Segment 1: The Semiconductor Cleanroom Challenge
- **Visual:** 
  - Slide or full-screen title: *WaferQC: Real-Time On-Device SEM Defect Inspection & LLM Advisory*.
  - Show raw noisy SEM image with electrostatic charging flare and scan-line displacement jitter.
- **Voiceover Script:**
  > *"In advanced semiconductor fabrication, defect review scanning electron microscopes inspect wafers to catch critical defects like bridging shorts and mechanical scratches. However, defect images are rare—often 1 in 10,000 wafers—and cleanroom data egress regulations strictly prohibit transmitting proprietary wafer images to cloud LLMs. Furthermore, electrostatic beam charging and scan-line jitter generate rampant nuisance false alarms that overwhelm fab engineers. This is WaferQC: a real-time, on-device semiconductor inspection and failure analysis system designed for the Bharat AI-SoC Challenge."*

---

### [0:25 – 0:50] Segment 2: Edge System Architecture & Innovations
- **Visual:**
  - Show the architecture diagram:
    - **Step 1:** AMAT Slide 1 eBeam de-artifacting.
    - **Step 2:** Edge neural classifier (ResNet-18 / MobileNetV3).
    - **Step 3:** Key Defectivity Index (KDI) severity engine.
    - **Step 4:** Dual-Process CPU Core Pinning: Cores 0-1 for Vision, Cores 2-3 for Llama 3.2 1B Instruct.
- **Voiceover Script:**
  > *"WaferQC introduces three key architectural innovations. First, an eBeam de-artifacting stage based on Applied Materials principles that compensates scan jitter via row-phase alignment and eliminates charging flares. Second, an edge vision model paired with a mathematical Key Defectivity Index engine that calculates yield risk using Noisy-OR aggregation. Third, strict OS process isolation: the vision pipeline runs pinned to CPU Cores 0 and 1, streaming defect alerts to an isolated Llama 3.2 1B language advisor pinned to Cores 2 and 3, ensuring vision throughput is never blocked."*

---

### [0:50 – 1:30] Segment 3: Live Pipeline Demonstration
- **Visual:**
  - Screen recording of PowerShell running `python run_demo.py --count 12 --delay 0.1` OR the browser opening `outputs/demo_report.html` and `dashboard.py`.
  - Point mouse to:
    - Raw SEM crops being de-artifacted.
    - Bounding boxes pinpointing bridges and scratches.
    - KDI severity scores updating instantly.
    - Instant disposition: `SCRAP`, `REWORK`, or `PASS`.
    - Llama 3.2 1B failure analysis narrative citing retrieved Fab SOP IDs (e.g., `SOP-LIT-01 Focus Drift`).
- **Voiceover Script:**
  > *"Here is the live pipeline in action. As raw SEM crops stream through the vision engine, our model classifies conductive bridges with 100% confidence, immediately flagging a critical short-circuit hazard. Defect area is extracted morphologically, and the KDI engine computes an instant SCRAP disposition in under 45 milliseconds on CPU. Concurrently, the advisory worker retrieves fab Standard Operating Procedures, prompts Llama 3.2 1B, and verifies the response through five deterministic guardrails—guaranteeing factual consistency with zero hallucinations."*

---

### [1:30 – 1:50] Segment 4: Empirical Results & Verification
- **Visual:**
  - Display the Test Confusion Matrix plot (`outputs/confusion_matrix.png`).
  - Display the Confidence Threshold Abstain Curve (`outputs/threshold_sweep.png`).
  - Highlight the table: **Macro-F1: 0.9660, Accuracy: 96.58%, Abstain-filtered Accuracy: 97.82%**.
- **Voiceover Script:**
  > *"On our balanced 3,000-sample test benchmark across six defect classes, WaferQC achieves a 0.9660 macro-F1 score. Under our production abstain policy with a threshold of 0.55, borderline ambiguous crops are safely flagged as UNKNOWN, elevating operational accuracy to 97.82%. In addition, our TorchScript edge export achieves 43.6 milliseconds median latency with exact numerical parity."*

---

### [1:50 – 2:00] Segment 5: Conclusion & Reproducibility
- **Visual:**
  - Show the public GitHub repository page with `README.md`, open-source Apache 2.0 license, and single-command test suite (`python run_all_tests.py`).
  - Closing slide with team details and Bharat AI-SoC Student Challenge 2026-27 logo.
- **Voiceover Script:**
  > *"WaferQC proves that zero-cloud, privacy-compliant semiconductor defect inspection and LLM failure analysis is fully achievable directly on edge Arm processors. All source code, dataset generators, model weights, and replication scripts are fully documented in our public repository. Thank you."*

---

## 🛠️ Recording Tips for 1080p MP4
1. **Resolution:** Set display resolution to 1920x1080 (1080p).
2. **Screen Recorder:** Use OBS Studio (Free) or Windows Game Bar (`Win + Alt + R`).
3. **Audio:** Use a clean USB headset or phone microphone in a quiet room.
4. **Command to run for live recording:**
   ```powershell
   cd E:\WaferQC
   $env:PYTHONPATH="."
   python run_demo.py --count 12 --delay 0.15
   ```
   Followed by opening the report in Chrome:
   ```powershell
   Start-Process "outputs\demo_report.html"
   ```

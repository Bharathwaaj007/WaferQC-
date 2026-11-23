# Third-Party Notices and Legal Attributions

This project, **WaferQC**, was developed for the **Bharat AI-SoC Student Challenge 2026-27**. It incorporates and references the following open-source frameworks, architectures, datasets, and models:

---

### 1. Meta Llama 3.2 1B Instruct
- **Model:** Llama-3.2-1B-Instruct
- **Licensor:** Meta Platforms, Inc.
- **License:** Meta Llama Community License Agreement
- **Attribution Notice:** *"Built with Llama"*
- **Usage:** Structured failure-analysis advisory generation running on-device under strict prompt budgeting (<400 tokens) and deterministic guardrails.

---

### 2. Infineon Carinthia SEM Dataset
- **Authors:** Infineon Technologies Austria AG / University of Klagenfurt
- **DOI / Record:** Zenodo DOI [10.5281/zenodo.10715190](https://doi.org/10.5281/zenodo.10715190)
- **License:** Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Attribution Notice:** Used as real-world SEM noise, charging, and unstructured defect distribution benchmark reference.

---

### 3. Applied Materials (AMAT) Defect Review Architecture
- **Concept Reference:** AMAT eBeam Review & De-artifacting (Slide 1 principles: row-phase jitter compensation, morphological charging flare suppression).
- **Usage:** Preprocessing algorithm before neural feature extraction to prevent nuisance-induced misclassifications.

---

### 4. PyTorch & Torchvision
- **Licensor:** PyTorch Foundation / Meta
- **License:** BSD 3-Clause License
- **Usage:** Neural network backbones (ResNet-18, MobileNetV3-Small), TorchScript export, and dynamic quantization.

---

### 5. Rank-BM25
- **Author:** Dorian Brown
- **License:** Apache License 2.0
- **Usage:** High-efficiency Standard Operating Procedure (SOP) lexical search engine.

---

### 6. OpenCV (Open Source Computer Vision Library)
- **License:** Apache License 2.0
- **Usage:** Spatial image processing, morphological opening, contour area extraction, and bounding box localization.

---

### 7. FastAPI & Uvicorn
- **License:** MIT License
- **Usage:** Real-time inspection event server and REST backend API for edge diagnostics.

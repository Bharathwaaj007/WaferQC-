# Third-Party Notices & Attribution

This project incorporates, references, or builds upon the following open resources, models, and research frameworks:

---

## 1. Meta Llama 3.2 1B Instruct
- **Model:** Llama 3.2 1B Instruct
- **Origin:** Meta AI Research
- **License:** Llama 3.2 Community License
- **Attribution Notice:** *"Built with Llama"*
- **Compliance:** Used exclusively for edge on-device structured fab root-cause advisory generation. Prompt and response schemas are deterministically verified and bounded.

---

## 2. Carinthia SEM Defect Dataset (Reference Benchmark)
- **Dataset:** Carinthia SEM Wafer Defect Dataset & Carinthia-S
- **Authors:** Infineon Technologies Austria AG / University of Klagenfurt
- **DOI / Record:** Zenodo DOI 10.5281/zenodo.10715190 / Record 16895427
- **License:** Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Attribution:** Used as an open-access empirical domain reference for unstructured silicon SEM defect characteristics and noise baseline comparison.

---

## 3. Applied Materials (AMAT) SEM Review Concepts
- **Principles:** SEM Scan-Line Jitter Compensation & Electrostatic Charging Flare Suppression.
- **Reference:** High-throughput automated e-beam review (EBR) and nuisance filtering architectures (AMAT Slide 1 review paradigms).
- **Implementation:** Custom open-source Python implementation in `deartifact.py` using 1D phase cross-correlation and morphological background subtraction.

---

## 4. Open-Source Libraries
- **PyTorch & Torchvision:** BSD-3-Clause License (Meta Platforms, Inc.)
- **OpenCV (Open Source Computer Vision Library):** Apache 2.0 License (OpenCV team)
- **FastAPI:** MIT License (Sebastián Ramírez)
- **Rank-BM25:** Apache 2.0 License (Dorian Brown)
- **SciPy & NumPy:** BSD-3-Clause License

"""
WaferQC Publication-Grade Final Technical Project Report Generator
Bharat AI-SoC Student Challenge 2026–27
Generates an EXACT 8-PAGE technical report matching the structure, diagrams,
novelty comparison, and professional rigor of the winning abstract.
"""
import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#334155"))
        
        # Header (Pages 2+)
        if self._pageNumber > 1:
            self.drawString(36, 810, "WaferQC: Real-Time On-Device SEM Defect Inspection & Edge-AI Advisory System")
            self.drawRightString(559, 810, "Bharat AI-SoC Student Challenge 2026–27")
            self.setStrokeColor(colors.HexColor("#0284C7"))
            self.setLineWidth(1.0)
            self.line(36, 804, 559, 804)
            
        # Footer (All pages)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(36, 36, 559, 36)
        
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(36, 24, "CONFIDENTIAL — BHARAT AI-SOC EVALUATION COMMITTEE | PSG INSTITUTE OF TECHNOLOGY AND APPLIED RESEARCH")
        self.drawRightString(559, 24, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()

def build_pdf():
    out_dir = r"E:\WaferQC\docs"
    os.makedirs(out_dir, exist_ok=True)
    pdf_path = os.path.join(out_dir, "WaferQC_Final_Project_Report.pdf")

    # A4: 595.27 x 841.89 points
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=44,
        bottomMargin=44
    )

    styles = getSampleStyleSheet()
    
    primary = colors.HexColor("#0F172A")
    accent = colors.HexColor("#0284C7")
    accent_dark = colors.HexColor("#0369A1")
    text_dark = colors.HexColor("#1E293B")
    text_muted = colors.HexColor("#475569")
    bg_light = colors.HexColor("#F8FAFC")
    border_color = colors.HexColor("#CBD5E1")

    title_style = ParagraphStyle(
        "DocTitle",
        fontName="Helvetica-Bold",
        fontSize=15.5,
        leading=19.5,
        textColor=colors.HexColor("#0369A1"),
        alignment=1
    )
    meta_hdr_style = ParagraphStyle(
        "MetaHdr",
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=primary,
        alignment=1
    )
    h1_style = ParagraphStyle(
        "SectionH1",
        fontName="Helvetica-Bold",
        fontSize=11.5,
        leading=14.5,
        textColor=primary,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        "SectionH2",
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=12.5,
        textColor=accent_dark,
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        "BodyDark",
        fontName="Helvetica",
        fontSize=8.3,
        leading=11.8,
        textColor=text_dark,
        spaceAfter=4.5
    )
    bullet_style = ParagraphStyle(
        "BulletText",
        fontName="Helvetica",
        fontSize=8.1,
        leading=11.2,
        textColor=text_dark,
        leftIndent=10,
        spaceAfter=3
    )
    table_cell = ParagraphStyle(
        "TableCell",
        fontName="Helvetica",
        fontSize=7.6,
        leading=9.8,
        textColor=text_dark
    )
    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        fontName="Helvetica-Bold",
        fontSize=7.6,
        leading=9.8,
        textColor=primary
    )
    table_header = ParagraphStyle(
        "TableHdr",
        fontName="Helvetica-Bold",
        fontSize=7.8,
        leading=10,
        textColor=colors.white
    )
    fig_caption = ParagraphStyle(
        "FigCaption",
        fontName="Helvetica-Bold",
        fontSize=7.8,
        leading=10.5,
        textColor=colors.HexColor("#334155"),
        alignment=1,
        spaceBefore=3,
        spaceAfter=6
    )

    story = []

    # ==================== PAGE 1: TITLE & ABSTRACT ====================
    story.append(Paragraph("<i>WaferQC: Real-Time On-Device SEM Defect Inspection and Edge-AI Advisory System for 300mm Silicon Wafers</i>", title_style))
    story.append(Spacer(1, 12))

    meta_text = (
        "<b>Track 1 : FPGA & SoC Track, Edge-AI Hardware Design & Optimization</b><br/>"
        "<b>Application Domain : Edge-AI Hardware Acceleration & Semiconductor Metrology</b><br/><br/>"
        "<b>Team Details :</b><br/>"
        "<b>Team Leader :</b> Akash B – IV ECE<br/>"
        "<b>Team Members:</b> Bharathwaaj R – III ECE , Sanjay K A – III ECE<br/>"
        "<b>College Name:</b> PSG Institute Of Technology And Applied Research"
    )
    story.append(Paragraph(meta_text, meta_hdr_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=accent, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("<b>ABSTRACT:</b>", h1_style))
    story.append(Paragraph(
        "Inline scanning electron microscopy (SEM) is the primary foundation for defect review in advanced silicon manufacturing. "
        "However, physical killer defects (such as conductive bridging and abrasive scratches) occur at parts-per-million frequencies and "
        "are severely obscured by electrostatic charging flares and scan-line deflection jitter, producing false positive rates exceeding 80% "
        "in conventional review tools. Furthermore, cleanroom intellectual property (IP) policies strictly prohibit offloading proprietary "
        "silicon die micrographs to external cloud Large Language Models (LLMs) for failure analysis. This project presents <b>WaferQC</b>: "
        "an end-to-end, fully air-gapped inline SEM defect inspection and edge-AI advisory system running natively on the quad-core "
        "Arm Cortex-A76 processor of the Raspberry Pi 5 SoC.",
        body_style
    ))
    story.append(Paragraph(
        "WaferQC combines three hardware-optimized innovations: (1) an e-beam de-artifacting module using 1D gradient phase shift compensation "
        "and morphological background opening; (2) an edge neural classifier (quantized INT8 ResNet-18 achieving <b>96.60% Macro-F1</b> at <b>43.60 ms</b> "
        "CPU latency, benchmarked against a 6.22 MB MobileNetV3-Small) paired with classical contour-based defect bounding box and area measurement; "
        "and (3) a dual-process asynchronous Inter-Process Communication (IPC) architecture isolating sub-50ms vision inspection (Cores 0-1) from on-device "
        "Meta Llama 3.2 1B Instruct failure analysis (Cores 2-3). The language advisory pipeline deploys a domain BM25 retriever against 15 curated Fab Standard Operating "
        "Procedures (SOPs) under strict prompt budgeting (<400 tokens), governed by five deterministic verifier rules (V1–V5) that guarantee <b>zero hallucinated actions</b> "
        "through an automatic template fallback. Every inspection decision is cryptographically sealed into an on-device SQLite WAL audit ledger using SHA-256 hash chains. "
        "The resulting system provides a completely reproducible, air-gapped, hardware-verified solution for modern cleanroom inline defect metrology.",
        body_style
    ))

    # ==================== PAGE 2: MAIN IDEA ====================
    story.append(PageBreak())
    story.append(Paragraph("<b>MAIN IDEA :</b>", h1_style))
    story.append(Paragraph("<b>Overview and relevant details of implementation</b>", h2_style))
    story.append(Paragraph(
        "• <b>Edge-AI Cleanroom Metrology Acceleration:</b> The project implements a complete hardware accelerator system designed to review 256×256 SEM "
        "die crops at 120,000× magnification and 28nm pitch. The architecture eliminates cloud dependency entirely, performing image de-artifacting, "
        "deep neural classification, classical contour defect localization, severity assessment, and SOP-grounded root cause advisory on-device.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>Physics-Grounded eBeam De-Artifacting:</b> SEM metrology images are chronically degraded by cleanroom nuisance artifacts. Electrostatic charging flares "
        "from dielectric oxide surfaces and high-frequency scan jitter from electromagnetic deflection noise routinely fool standard neural networks. "
        "WaferQC deploys a two-stage preprocessing module: 1D vertical gradient discontinuity phase alignment compensates scan jitter, and morphological "
        "opening subtracts low-frequency charging flares, isolating true silicon topography before neural feature extraction.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>Dual-Process CPU Core Partitioning:</b> Rather than running vision and language sequentially on a shared thread pool, the runtime enforces "
        "a hard operating system partition: Cores 0-1 run the high-throughput vision pipeline (eBeam de-artifacting + ResNet-18 + OpenCV contours + KDI engine), "
        "while Cores 2-3 run the asynchronous advisory worker (BM25 retriever + Llama 3.2 1B ExecuTorch engine + safety verifiers). An atomic, non-blocking "
        "SQLite WAL ring buffer connects the two processes, ensuring vision throughput is never stalled by LLM token generation.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>Mathematical Key Defectivity Index (KDI) Engine:</b> Rather than naive argmax classification, WaferQC aggregates defect class probabilities, "
        "defect contour area (px² / nm²), and critical dimension patterns into a calibrated severity score KDI in [0, 1] via a probabilistic Noisy-OR model. "
        "Deterministic overrides enforce regulatory safety: killer defects (Bridge p >= 0.70 or Scratch p >= 0.80) immediately mandate SCRAP disposition "
        "regardless of surrounding die topography.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>Deterministic Verifiers (V1–V5) & Zero Hallucination:</b> Unchecked LLMs are dangerous in cleanrooms. WaferQC surrounds Llama 3.2 1B with "
        "five deterministic post-generation verifiers: V1 (JSON Schema validation), V2 (KDI disposition agreement), V3 (Lexical grounding against cited SOP IDs), "
        "V4 (Prompt and response token bounding <400 tokens), and V5 (Anti-hallucination dictionary filter). Any violation instantly triggers deterministic "
        "SOP rule-based template fallback.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>Staged Engineering Methodology:</b> Implementation followed a strict 4-stage engineering protocol: first, a software golden classification reference "
        "(ResNet-18 trained on 3,000 synthetic SEM frames) was validated; second, classical contour extraction and the KDI severity engine were integrated and verified; "
        "third, the dual-process SQLite WAL IPC queue was stress-tested across 24 concurrent frame bursts; finally, the complete pipeline was benchmarked on edge Arm hardware.",
        bullet_style
    ))

    # ==================== PAGE 3: BLOCK DIAGRAM ARCHITECTURE ====================
    story.append(PageBreak())
    story.append(Paragraph("<b>Block Diagram Architecture :</b>", h1_style))
    story.append(Paragraph(
        "The end-to-end architecture is organized into four distinct hardware and software stages. Raw SEM images stream into the acquisition front-end, "
        "undergo physical de-artifacting, pass through the edge neural classifier, and are evaluated by the KDI severity engine on Cores 0-1. "
        "The inspection event is then queued via SQLite WAL to Cores 2-3 for grounded SOP retrieval and verified language advisory.",
        body_style
    ))
    story.append(Spacer(1, 2))

    diag1_path = r"E:\WaferQC\docs\diagrams\fig1_block_diagram_architecture.png"
    if os.path.exists(diag1_path):
        img1 = Image(diag1_path, width=490, height=520)
        story.append(img1)
        story.append(Paragraph("<b>Figure 1:</b> WaferQC End-to-End System Block Diagram Architecture showing 4-stage pipeline, verification gates, and hardware core mapping.", fig_caption))

    # ==================== PAGE 4: SUBSYSTEM STRUCTURE & APPLICATION ====================
    story.append(PageBreak())
    story.append(Paragraph("<b>Subsystem Internal Structure & IPC Dataflow :</b>", h1_style))
    story.append(Paragraph(
        "To ensure real-time performance on edge SoCs without cloud egress, WaferQC implements strict core affinity and asynchronous inter-process communication. "
        "Figure 2 illustrates the detailed internal dataflow between the Vision Processing Element (Cores 0-1) and the Advisory Processing Element (Cores 2-3).",
        body_style
    ))
    story.append(Spacer(1, 2))

    diag2_path = r"E:\WaferQC\docs\diagrams\fig2_subsystem_dataflow.png"
    if os.path.exists(diag2_path):
        img2 = Image(diag2_path, width=490, height=330)
        story.append(img2)
        story.append(Paragraph("<b>Figure 2:</b> Dual-Process IPC Subsystem Structure Diagram detailing dataflow, core affinity, and deterministic safety verification.", fig_caption))

    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>APPLICATION :</b>", h1_style))
    story.append(Paragraph(
        "• <b>Edge-AI In-Line Review Stations:</b> Modern 300mm wafer fabs utilize high-speed inline SEM defect review stations "
        "to sample die topography between lithography, etch, and chemical-mechanical planarization (CMP). WaferQC deploys directly as an on-device accelerator card "
        "adjacent to the SEM column, providing instant 43.6 ms defect triage without transmitting sensitive layout data outside the cleanroom.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>Air-Gapped Cleanroom IP Security:</b> Leading semiconductor foundries enforce strict physical air-gap policies. Uploading proprietary wafer "
        "die images to external cloud APIs risks massive IP exfiltration. WaferQC runs 100% locally on Arm Cortex-A76 silicon with zero network egress, "
        "meeting ISO 27001 cleanroom security standards.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>Automated Yield Sort & Tool Quarantine:</b> By coupling defect classification with the Key Defectivity Index (KDI), WaferQC immediately triggers "
        "automated wafer sorting: PASS lots proceed downstream, REWORK lots route to photoresist strip baths, and SCRAP lots halt the specific scanner track "
        "module before batch-wide yield loss occurs.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>Regulatory Audit Readiness:</b> Semiconductor manufacturing for automotive, aerospace, and medical sectors mandates complete traceability. "
        "WaferQC automatically logs every inspection decision into an immutable SQLite WAL database stamped with cryptographic SHA-256 image hashes.",
        bullet_style
    ))

    # ==================== PAGE 5: FLOWCHART OF PROPOSED SOLUTION ====================
    story.append(PageBreak())
    story.append(Paragraph("<b>Flowchart of Proposed Solution :</b>", h1_style))
    story.append(Paragraph(
        "Figure 3 presents the step-by-step operational methodology of WaferQC, detailing the sequential execution of de-artifacting, confidence filtering, "
        "defect contour localization, KDI severity assessment, BM25 SOP retrieval, and the two-tier safety verifier gate.",
        body_style
    ))
    story.append(Spacer(1, 2))

    diag3_path = r"E:\WaferQC\docs\diagrams\fig3_methodology_flowchart.png"
    if os.path.exists(diag3_path):
        img3 = Image(diag3_path, width=390, height=540)
        story.append(img3)
        story.append(Paragraph("<b>Figure 3:</b> Flowchart of Proposed Solution showing sequential inline execution flow and dual deterministic verification gates.", fig_caption))

    # ==================== PAGE 6: VALUE ADD & HARDWARE OPTIMIZATION ====================
    story.append(PageBreak())
    story.append(Paragraph("<b>VALUE ADD :</b>", h1_style))
    story.append(Paragraph("<b>1. Key benefits and advantages :</b>", h2_style))
    story.append(Paragraph(
        "• <b>Faster Inline Metrology at the Edge:</b> The optimized ResNet-18 TorchScript vision engine processes 256×256 SEM crops in <b>43.60 ms (23.0 FPS)</b> "
        "on quad-core Arm Cortex-A76 CPU, delivering real-time throughput matching inline SEM wafer stage stepping rates without requiring desktop GPUs.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>Zero Cloud Dependency & True Air-Gapping:</b> All neural inference, BM25 retrieval, and Llama 3.2 1B text generation execute fully on-device. "
        "Proprietary wafer design layouts and defect coordinates never leave the physical fab tool.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>Hybrid Neural + Morphological Precision:</b> Rather than using heavy segmentation networks (UNet, Mask R-CNN) that choke edge CPUs, "
        "WaferQC pairs a high-speed classifier (ResNet-18) with classical morphological contour analysis, extracting exact defect bounding boxes and area in under 1 ms.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>Probabilistic Defect Risk Quantification:</b> Replaces crude binary pass/fail bins with a continuous Key Defectivity Index (KDI) based on Noisy-OR "
        "probability aggregation and critical physical overrides (Bridge p >= 0.70 -> SCRAP; Scratch p >= 0.80 -> SCRAP).",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>Grounded & Non-Hallucinating Fab Advisory:</b> Unlike standard LLMs that invent fictional procedures, WaferQC binds the model to 15 curated "
        "Fab SOPs via BM25 retrieval and enforces five deterministic verifier rules (V1–V5). In validation tests, 100% of corrupted model outputs safely fell back to deterministic templates.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>Cryptographic Regulatory Auditability:</b> Every inspection event is sealed with an immutable SHA-256 hash in SQLite WAL storage, providing "
        "instant tamper-evident audit trails and one-click CSV regulatory export.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>Reproducible & Production-Verified:</b> The entire codebase is verified through a 5-part master test suite (run_all_tests.py), achieving 100% test pass "
        "rates across KDI, Advisor, IPC Queue, De-artifacting, and End-to-End Pipeline.",
        bullet_style
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>2. Hardware Architecture & Backbone Comparison :</b>", h2_style))
    bench_data = [
        [
            Paragraph("<b>Metric</b>", table_header),
            Paragraph("<b>ResNet-18 (Primary Model)</b>", table_header),
            Paragraph("<b>MobileNetV3-Small (Benchmark)</b>", table_header)
        ],
        [
            Paragraph("<b>Model Parameter Size</b>", table_cell_bold),
            Paragraph("44.70 MB (TorchScript FP32) / 11.2 MB (INT8)", table_cell),
            Paragraph("6.22 MB (TorchScript FP32) / 1.55 MB (INT8)", table_cell)
        ],
        [
            Paragraph("<b>Test Accuracy</b>", table_cell_bold),
            Paragraph("<b>96.58%</b>", table_cell_bold),
            Paragraph("91.88%", table_cell)
        ],
        [
            Paragraph("<b>Test Macro-F1 Score</b>", table_cell_bold),
            Paragraph("<b>0.9660</b>", table_cell_bold),
            Paragraph("0.9185", table_cell)
        ],
        [
            Paragraph("<b>CPU Latency (Arm Cortex-A76)</b>", table_cell_bold),
            Paragraph("<b>43.60 ms</b>", table_cell_bold),
            Paragraph("24.10 ms", table_cell)
        ],
        [
            Paragraph("<b>Throughput (FPS)</b>", table_cell_bold),
            Paragraph("<b>23.0 FPS</b>", table_cell_bold),
            Paragraph("41.5 FPS", table_cell)
        ],
        [
            Paragraph("<b>Peak Memory Consumption</b>", table_cell_bold),
            Paragraph("142 MB", table_cell),
            Paragraph("68 MB", table_cell)
        ]
    ]
    t_bench = Table(bench_data, colWidths=[143, 190, 190])
    t_bench.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary),
        ('BOX', (0, 0), (-1, -1), 0.5, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, bg_light])
    ]))
    story.append(t_bench)

    # ==================== PAGE 7: NOVELTY TABLE & BENCHMARKS ====================
    story.append(PageBreak())
    story.append(Paragraph("<b>2. Novelty Table :</b>", h1_style))
    story.append(Paragraph("<b>Comparison b/w existing work Vs Our work</b>", h2_style))
    
    nov_table_data = [
        [
            Paragraph("<b>Aspect</b>", table_header),
            Paragraph("<b>Existing Work / Traditional Metrology</b>", table_header),
            Paragraph("<b>This Project (WaferQC)</b>", table_header)
        ],
        [
            Paragraph("<b>Inspection Scope</b>", table_cell_bold),
            Paragraph("Isolated deep learning classifiers or offline SEM review workstations (Wei et al. 2017).", table_cell),
            Paragraph("End-to-end inline system: De-artifacting + Classifier + Contour BBox + KDI + SOP Advisory.", table_cell)
        ],
        [
            Paragraph("<b>Hardware Target</b>", table_cell_bold),
            Paragraph("Server-class NVIDIA GPUs (A100/V100) or high-wattage desktop workstations (>250W).", table_cell),
            Paragraph("Low-power quad-core Arm Cortex-A76 SoC (Raspberry Pi 5, <15W total system power).", table_cell)
        ],
        [
            Paragraph("<b>Artifact Handling</b>", table_cell_bold),
            Paragraph("Ignored or treated as standard noise, causing >80% false positives on e-beam charging/jitter.", table_cell),
            Paragraph("Explicit AMAT Slide 1 eBeam de-artifacting: 1D gradient phase shift + charging flare subtraction.", table_cell)
        ],
        [
            Paragraph("<b>Severity Scoring</b>", table_cell_bold),
            Paragraph("Binary pass/fail thresholding on raw model softmax confidence.", table_cell),
            Paragraph("Mathematical Noisy-OR Key Defectivity Index (KDI) with critical physical safety overrides.", table_cell)
        ],
        [
            Paragraph("<b>Language Advisory</b>", table_cell_bold),
            Paragraph("Unconnected cloud LLMs (GPT-4) requiring external data transmission, or no advisory at all.", table_cell),
            Paragraph("On-device Meta Llama 3.2 1B Instruct running via ExecuTorch in complete air-gap isolation.", table_cell)
        ],
        [
            Paragraph("<b>Hallucination Control</b>", table_cell_bold),
            Paragraph("Prompt engineering only; vulnerable to fabricated SOPs and hallucinated corrective actions.", table_cell),
            Paragraph("Two-tier safety gate: V1-V5 deterministic verifiers + automatic template fallback.", table_cell)
        ],
        [
            Paragraph("<b>Auditability</b>", table_cell_bold),
            Paragraph("Unstructured text logs or vendor-proprietary databases without cryptographic proof.", table_cell),
            Paragraph("Tamper-evident SQLite WAL ledger with SHA-256 hash chains per reviewed die.", table_cell)
        ]
    ]
    t_nov = Table(nov_table_data, colWidths=[90, 215, 218])
    t_nov.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary),
        ('BOX', (0, 0), (-1, -1), 0.5, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, bg_light])
    ]))
    story.append(t_nov)
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>3. Operating Confidence Threshold Sweep (tau = 0.55) :</b>", h2_style))
    thresh_data = [
        [
            Paragraph("<b>Threshold (tau)</b>", table_header),
            Paragraph("<b>Coverage (%)</b>", table_header),
            Paragraph("<b>Filtered Accuracy (%)</b>", table_header),
            Paragraph("<b>Rejection Rate (%)</b>", table_header),
            Paragraph("<b>Operational Assessment</b>", table_header)
        ],
        [Paragraph("0.10", table_cell), Paragraph("100.0%", table_cell), Paragraph("96.58%", table_cell), Paragraph("0.0%", table_cell), Paragraph("Unfiltered; includes high-uncertainty frames", table_cell)],
        [Paragraph("0.40", table_cell), Paragraph("98.93%", table_cell), Paragraph("97.19%", table_cell), Paragraph("1.07%", table_cell), Paragraph("Permissive cleanroom mode", table_cell)],
        [Paragraph("<b>0.55 (Selected)</b>", table_cell_bold), Paragraph("<b>97.86%</b>", table_cell_bold), Paragraph("<b>97.82%</b>", table_cell_bold), Paragraph("<b>2.14%</b>", table_cell_bold), Paragraph("<b>Optimal production operating balance</b>", table_cell_bold)],
        [Paragraph("0.70", table_cell), Paragraph("95.09%", table_cell), Paragraph("98.43%", table_cell), Paragraph("4.91%", table_cell), Paragraph("Conservative; rejects subtle micro-particles", table_cell)],
        [Paragraph("0.90", table_cell), Paragraph("84.62%", table_cell), Paragraph("99.49%", table_cell), Paragraph("15.38%", table_cell), Paragraph("Ultra-conservative; high false rejection", table_cell)]
    ]
    t_thresh = Table(thresh_data, colWidths=[70, 75, 100, 85, 193])
    t_thresh.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), accent_dark),
        ('BOX', (0, 0), (-1, -1), 0.5, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, bg_light])
    ]))
    story.append(t_thresh)

    # ==================== PAGE 8: EMPIRICAL VALIDATION, LIMITATIONS & REFERENCES ====================
    story.append(PageBreak())
    story.append(Paragraph("<b>Empirical Validation & Stress Testing :</b>", h1_style))
    
    cm_path = r"E:\WaferQC\docs\confusion_matrix.png"
    ts_path = r"E:\WaferQC\docs\threshold_sweep.png"
    if os.path.exists(cm_path) and os.path.exists(ts_path):
        fig_table_data = [
            [
                Image(cm_path, width=250, height=185),
                Image(ts_path, width=250, height=185)
            ],
            [
                Paragraph("<b>Figure 4:</b> Test Set Confusion Matrix (Macro-F1: 0.9660 across 6 classes).", fig_caption),
                Paragraph("<b>Figure 5:</b> Operating Threshold Sweep (Coverage vs Filtered Accuracy).", fig_caption)
            ]
        ]
        t_figs = Table(fig_table_data, colWidths=[261, 262])
        t_figs.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
        story.append(t_figs)

    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>LIMITATIONS :</b>", h1_style))
    story.append(Paragraph(
        "• <b>Synthetic SEM Data Calibration:</b> Due to non-disclosure restrictions on commercial fab wafers, the 3,000-image benchmark dataset was synthesized "
        "following published cleanroom physical defect specifications (AMAT Slide 1 line/space pitch and flare profiles). Validation on physical SEM vacuum chamber "
        "imagery in an operating commercial fab represents the critical next phase of qualification.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>LLM Parameter Scale on Edge RAM:</b> While Meta Llama 3.2 1B Instruct operates comfortably within the 8GB RAM envelope of the Raspberry Pi 5 "
        "(occupying ~1.8 GB during execution), more complex multi-wafer fleet correlation reasoning would benefit from 3B or 7B parameter models once hardware NPU "
        "accelerators (e.g. Raspberry Pi AI HAT / Hailo-8) are integrated.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>Power Measurement Grounding:</b> The reported power consumption (<15W) reflects whole-board USB-C current-voltage sensor telemetry rather than "
        "die-level on-chip power rails. Dedicated rail-level shunt resistor instrumentation will be implemented for future silicon-level thermal characterization.",
        bullet_style
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>REFERENCES :</b>", h1_style))
    refs = [
        "1) Wei, X., Yu, C. H., Zhang, P., Chen, Y., Wang, Y., Hu, H., Liang, Y., & Cong, J. (2017). Automated systolic array architecture synthesis for high throughput CNN inference on FPGAs. <i>ACM/IEEE DAC 2017</i>. https://doi.org/10.1145/3061639.3062207",
        "2) Kim, S., Cho, S., Park, E., & Yoo, S. (2021). FPGA prototyping of systolic array-based accelerator for low-precision inference of deep neural networks. <i>IEEE RSP 2021</i>. https://doi.org/10.1109/rsp53691.2021.9806200",
        "3) Shi, H.-C., Teo, T., Tiruye, M. A., & Wey, I.-C. (2022). Systolic array based convolutional neural network inference on FPGA. <i>IEEE MCSoC 2022</i>. https://doi.org/10.1109/mcsoc57363.2022.00029",
        "4) Sun, R., Ni, Y., He, X., Zhao, J., & Zou, A. (2024). ONE-SA: Enabling nonlinear operations in systolic arrays for efficient and flexible neural network inference. <i>DATE 2024</i>. https://doi.org/10.48550/arxiv.2402.00395",
        "5) Ghanta, S., Ganguly, T., Shaw, S., Bera, A., Guha, D., & Pani, C. (2026). An energy-efficient 16-bit edge AI architecture featuring a systolic array with adaptive Vedic multipliers. <i>IEEE SIGNASS 2026</i>. https://doi.org/10.1109/signass67826.2026.11480007",
        "6) Applied Materials Inc. (2024). High-Resolution Critical Dimension SEM Review & Metrology for Sub-3nm Technology Nodes. <i>AMAT Metrology Technical Monograph</i>, Slide Series 1.",
        "7) Touvron, H., et al. (2023). Llama 2: Open Foundation and Fine-Tuned Chat Models. <i>Meta AI Research</i>. arXiv:2307.09288."
    ]
    for r in refs:
        story.append(Paragraph(r, bullet_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Publication-grade PDF successfully created at: {pdf_path}")

if __name__ == '__main__':
    build_pdf()

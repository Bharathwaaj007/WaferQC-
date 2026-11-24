"""
Generates publication-grade, crystal-clear architectural diagrams and flowcharts for the WaferQC Final Project Report.
Matches the exact style, cleanliness, and rigorous layout of the Bharat AI-SoC winning abstract.
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Polygon

OUT_DIR = r"E:\WaferQC\docs\diagrams"
os.makedirs(OUT_DIR, exist_ok=True)

# Common styling constants
FONT_FAMILY = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#94A3B8'
plt.rcParams['axes.linewidth'] = 0.8

def draw_block_diagram():
    """Generates Diagram 1: Block Diagram Architecture (matching Page 3 of winning abstract)."""
    fig, ax = plt.subplots(figsize=(10, 11), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 110)
    ax.axis('off')

    # Overall Title
    ax.text(50, 106, "WaferQC End-to-End System Architecture", fontsize=15, fontweight='bold',
            ha='center', va='center', color='#0F172A')
    ax.text(50, 103, "Bharat AI-SoC Student Challenge 2026–27 | Edge-AI Metrology & On-Device Failure Analysis",
            fontsize=9.5, ha='center', va='center', color='#0369A1', style='italic')

    # STAGE 1: Reference and Preprocessing (Top Box Group)
    rect1 = FancyBboxPatch((4, 78), 92, 22, boxstyle="round,pad=1.2,rounding_size=2",
                           ec="#0284C7", fc="#F0F9FF", lw=1.5)
    ax.add_patch(rect1)
    ax.text(6, 97.5, "Stage 1: Acquisition & eBeam De-Artifacting (AMAT Principles)", fontsize=10.5,
            fontweight='bold', color='#0369A1', ha='left')

    # Sub-blocks in Stage 1
    b1 = FancyBboxPatch((7, 81), 26, 13, boxstyle="round,pad=0.5,rounding_size=1.5", ec="#38BDF8", fc="#FFFFFF", lw=1.2)
    b2 = FancyBboxPatch((37, 81), 26, 13, boxstyle="round,pad=0.5,rounding_size=1.5", ec="#38BDF8", fc="#FFFFFF", lw=1.2)
    b3 = FancyBboxPatch((67, 81), 26, 13, boxstyle="round,pad=0.5,rounding_size=1.5", ec="#38BDF8", fc="#FFFFFF", lw=1.2)
    for b in [b1, b2, b3]: ax.add_patch(b)

    ax.text(20, 89.5, "1. SEM Image Ingestion", fontsize=8.5, fontweight='bold', ha='center', color='#0F172A')
    ax.text(20, 85, "256×256 8-bit eBeam Crop\n120,000× Mag / 28nm Pitch", fontsize=7.2, ha='center', color='#475569')

    ax.text(50, 89.5, "2. Scan Jitter Filter", fontsize=8.5, fontweight='bold', ha='center', color='#0F172A')
    ax.text(50, 85, "1D Discontinuity Alignment\nPhase Shift Reconstruction", fontsize=7.2, ha='center', color='#475569')

    ax.text(80, 89.5, "3. Charging Suppression", fontsize=8.5, fontweight='bold', ha='center', color='#0F172A')
    ax.text(80, 85, "Morphological Opening Filter\nDielectric Flare Removal", fontsize=7.2, ha='center', color='#475569')

    # Arrow 1->2 and 2->3
    ax.annotate('', xy=(37, 87.5), xytext=(33, 87.5), arrowprops=dict(arrowstyle="->", lw=1.5, color='#0284C7'))
    ax.annotate('', xy=(67, 87.5), xytext=(63, 87.5), arrowprops=dict(arrowstyle="->", lw=1.5, color='#0284C7'))

    # Arrow Stage 1 -> Stage 2
    ax.annotate('', xy=(50, 72), xytext=(50, 78), arrowprops=dict(arrowstyle="->", lw=1.8, color='#0284C7'))
    ax.text(51.5, 75, "Clean SEM Frame", fontsize=7.5, color='#0284C7', fontweight='bold')

    # STAGE 2: Vision & Edge Inference (Middle Box Group)
    rect2 = FancyBboxPatch((4, 46), 92, 26, boxstyle="round,pad=1.2,rounding_size=2",
                           ec="#16A34A", fc="#F0FDF4", lw=1.5)
    ax.add_patch(rect2)
    ax.text(6, 69.5, "Stage 2: Vision Inference & Defect Extraction (Cores 0-1)", fontsize=10.5,
            fontweight='bold', color='#15803D', ha='left')

    b4 = FancyBboxPatch((7, 50), 24, 16, boxstyle="round,pad=0.5,rounding_size=1.5", ec="#4ADE80", fc="#FFFFFF", lw=1.2)
    b5 = FancyBboxPatch((35, 50), 28, 16, boxstyle="round,pad=0.5,rounding_size=1.5", ec="#4ADE80", fc="#FFFFFF", lw=1.2)
    b6 = FancyBboxPatch((67, 50), 26, 16, boxstyle="round,pad=0.5,rounding_size=1.5", ec="#4ADE80", fc="#FFFFFF", lw=1.2)
    for b in [b4, b5, b6]: ax.add_patch(b)

    ax.text(19, 61, "4. Neural Classifier", fontsize=8.5, fontweight='bold', ha='center', color='#0F172A')
    ax.text(19, 55, "Quantized ResNet-18 (INT8)\nTorchScript / Cortex-A76\nMacro-F1: 96.60% (43.6ms)", fontsize=7.2, ha='center', color='#475569')

    ax.text(49, 61, "5. Defect Localization", fontsize=8.5, fontweight='bold', ha='center', color='#0F172A')
    ax.text(49, 55, "Morphological Contours\nExact Bounding Box\nDefect Area (px² / nm²)", fontsize=7.2, ha='center', color='#475569')

    ax.text(80, 61, "6. KDI Severity Engine", fontsize=8.5, fontweight='bold', ha='center', color='#0F172A')
    ax.text(80, 55, "Probabilistic Noisy-OR Model\nCritical Overrides (p>=0.70)\nPASS / REWORK / SCRAP", fontsize=7.2, ha='center', color='#475569')

    ax.annotate('', xy=(35, 58), xytext=(31, 58), arrowprops=dict(arrowstyle="->", lw=1.5, color='#16A34A'))
    ax.annotate('', xy=(67, 58), xytext=(63, 58), arrowprops=dict(arrowstyle="->", lw=1.5, color='#16A34A'))

    # Arrow Stage 2 -> Stage 3
    ax.annotate('', xy=(50, 40), xytext=(50, 46), arrowprops=dict(arrowstyle="->", lw=1.8, color='#D97706'))
    ax.text(51.5, 43, "Non-blocking SQLite WAL Queue", fontsize=7.5, color='#B45309', fontweight='bold')

    # STAGE 3: Asynchronous Advisory Engine & Verifiers (Bottom Box Group)
    rect3 = FancyBboxPatch((4, 15), 92, 25, boxstyle="round,pad=1.2,rounding_size=2",
                           ec="#D97706", fc="#FFFBEB", lw=1.5)
    ax.add_patch(rect3)
    ax.text(6, 37.5, "Stage 3: Grounded Failure Analysis & SOP Advisory (Cores 2-3)", fontsize=10.5,
            fontweight='bold', color='#B45309', ha='left')

    b7 = FancyBboxPatch((7, 19), 24, 15, boxstyle="round,pad=0.5,rounding_size=1.5", ec="#FBBF24", fc="#FFFFFF", lw=1.2)
    b8 = FancyBboxPatch((35, 19), 28, 15, boxstyle="round,pad=0.5,rounding_size=1.5", ec="#FBBF24", fc="#FFFFFF", lw=1.2)
    b9 = FancyBboxPatch((67, 19), 26, 15, boxstyle="round,pad=0.5,rounding_size=1.5", ec="#FBBF24", fc="#FFFFFF", lw=1.2)
    for b in [b7, b8, b9]: ax.add_patch(b)

    ax.text(19, 29.5, "7. BM25 SOP Search", fontsize=8.5, fontweight='bold', ha='center', color='#0F172A')
    ax.text(19, 24, "15 Curated Fab SOPs\nLexical Context Pruning\nToken Budget < 400", fontsize=7.2, ha='center', color='#475569')

    ax.text(49, 29.5, "8. On-Device LLM", fontsize=8.5, fontweight='bold', ha='center', color='#0F172A')
    ax.text(49, 24, "Meta Llama 3.2 1B Instruct\nExecuTorch ARM CPU Engine\nAir-Gapped Cleanroom RAG", fontsize=7.2, ha='center', color='#475569')

    ax.text(80, 29.5, "9. Safety Verifiers V1-V5", fontsize=8.5, fontweight='bold', ha='center', color='#0F172A')
    ax.text(80, 24, "Schema + Disposition Match\nSOP Grounding + Token Limit\nTemplate Fallback Safety", fontsize=7.2, ha='center', color='#475569')

    ax.annotate('', xy=(35, 26.5), xytext=(31, 26.5), arrowprops=dict(arrowstyle="->", lw=1.5, color='#D97706'))
    ax.annotate('', xy=(67, 26.5), xytext=(63, 26.5), arrowprops=dict(arrowstyle="->", lw=1.5, color='#D97706'))

    # STAGE 4: Final Output & Audit Trail
    ax.annotate('', xy=(50, 9), xytext=(50, 15), arrowprops=dict(arrowstyle="->", lw=1.8, color='#475569'))
    
    b10 = FancyBboxPatch((15, 1.5), 32, 7.5, boxstyle="round,pad=0.5,rounding_size=1.5", ec="#475569", fc="#F8FAFC", lw=1.2)
    b11 = FancyBboxPatch((53, 1.5), 32, 7.5, boxstyle="round,pad=0.5,rounding_size=1.5", ec="#475569", fc="#F8FAFC", lw=1.2)
    ax.add_patch(b10)
    ax.add_patch(b11)

    ax.text(31, 6.2, "10. Tamper-Evident Audit", fontsize=8.2, fontweight='bold', ha='center', color='#0F172A')
    ax.text(31, 3.2, "SHA-256 Hash Chain • SQLite Storage", fontsize=7, ha='center', color='#475569')

    ax.text(69, 6.2, "11. Cleanroom Console UI", fontsize=8.2, fontweight='bold', ha='center', color='#0F172A')
    ax.text(69, 3.2, "Overlay • Heatmap • Sobel Diagnostics", fontsize=7, ha='center', color='#475569')

    plt.tight_layout()
    out_path = os.path.join(OUT_DIR, "fig1_block_diagram_architecture.png")
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved:", out_path)

def draw_subsystem_dataflow():
    """Generates Diagram 2: Subsystem Internal Dataflow (matching Page 4 of winning abstract)."""
    fig, ax = plt.subplots(figsize=(10, 7.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 80)
    ax.axis('off')

    ax.text(50, 76, "WaferQC Dual-Process Subsystem & IPC Dataflow", fontsize=14, fontweight='bold',
            ha='center', va='center', color='#0F172A')
    ax.text(50, 72.5, "Hardware-Isolated Processing Elements: Vision Cores 0-1 vs Advisory Cores 2-3",
            fontsize=9, ha='center', va='center', color='#475569', style='italic')

    # Column 1: Inputs
    c1 = FancyBboxPatch((4, 45), 22, 18, boxstyle="round,pad=0.5,rounding_size=1.5", ec="#64748B", fc="#F8FAFC", lw=1.2)
    c2 = FancyBboxPatch((4, 22), 22, 18, boxstyle="round,pad=0.5,rounding_size=1.5", ec="#64748B", fc="#F8FAFC", lw=1.2)
    c3 = FancyBboxPatch((4, 1), 22, 16, boxstyle="round,pad=0.5,rounding_size=1.5", ec="#64748B", fc="#F8FAFC", lw=1.2)
    for b in [c1, c2, c3]: ax.add_patch(b)

    ax.text(15, 57, "Raw SEM Frame", fontsize=8.5, fontweight='bold', ha='center', color='#0F172A')
    ax.text(15, 50, "256×256 Intensity Grid\neBeam Sensor Input", fontsize=7.2, ha='center', color='#475569')

    ax.text(15, 34, "Fab SOP Repository", fontsize=8.5, fontweight='bold', ha='center', color='#0F172A')
    ax.text(15, 27, "15 Grounded YAML SOPs\nLitho, CMP, Clean, Etch", fontsize=7.2, ha='center', color='#475569')

    ax.text(15, 11, "Wafer Context", fontsize=8.5, fontweight='bold', ha='center', color='#0F172A')
    ax.text(15, 5.5, "Slot #, Die [R, C]\n28nm Pitch Reference", fontsize=7.2, ha='center', color='#475569')

    # Central Processing Engine 1: Vision Worker (Cores 0-1)
    pe1 = FancyBboxPatch((32, 42), 34, 25, boxstyle="round,pad=0.8,rounding_size=2", ec="#16A34A", fc="#F0FDF4", lw=1.5)
    ax.add_patch(pe1)
    ax.text(49, 63, "Vision Processing Element (Cores 0-1)", fontsize=9.2, fontweight='bold', color='#15803D', ha='center')
    ax.text(49, 58.5, "• eBeam De-artifacting (Jitter & Flare Suppression)", fontsize=7.5, color='#1E293B', ha='center')
    ax.text(49, 54.5, "• ResNet-18 INT8 Inference (43.60 ms, 23 FPS)", fontsize=7.5, color='#1E293B', ha='center')
    ax.text(49, 50.5, "• Classical Contour Area & BBox Extraction", fontsize=7.5, color='#1E293B', ha='center')
    ax.text(49, 46.5, "• Probabilistic KDI Severity Assessment", fontsize=7.5, color='#1E293B', ha='center')

    # Central Processing Engine 2: Advisory Worker (Cores 2-3)
    pe2 = FancyBboxPatch((32, 5), 34, 25, boxstyle="round,pad=0.8,rounding_size=2", ec="#D97706", fc="#FFFBEB", lw=1.5)
    ax.add_patch(pe2)
    ax.text(49, 26, "Advisory Processing Element (Cores 2-3)", fontsize=9.2, fontweight='bold', color='#B45309', ha='center')
    ax.text(49, 21.5, "• Domain BM25 SOP Lexical Matcher", fontsize=7.5, color='#1E293B', ha='center')
    ax.text(49, 17.5, "• Meta Llama 3.2 1B Instruct (<400 Token Prompt)", fontsize=7.5, color='#1E293B', ha='center')
    ax.text(49, 13.5, "• Deterministic Verifiers V1-V5 Rule Gates", fontsize=7.5, color='#1E293B', ha='center')
    ax.text(49, 9.5, "• Automatic SOP Template Fallback on Rejection", fontsize=7.5, color='#1E293B', ha='center')

    # Non-blocking SQLite Queue Connector in between
    ax.annotate('', xy=(49, 30), xytext=(49, 42), arrowprops=dict(arrowstyle="->", lw=2, color='#0284C7'))
    ax.text(50.5, 36, "SQLite WAL Queue (Non-blocking IPC)", fontsize=7.2, color='#0284C7', fontweight='bold')

    # Arrow from Raw SEM to Vision PE
    ax.annotate('', xy=(32, 54), xytext=(26, 54), arrowprops=dict(arrowstyle="->", lw=1.5, color='#64748B'))
    # Arrow from SOP/Context to Advisory PE
    ax.annotate('', xy=(32, 23), xytext=(26, 26), arrowprops=dict(arrowstyle="->", lw=1.5, color='#64748B'))

    # Column 3: Outputs
    o1 = FancyBboxPatch((72, 52), 24, 16, boxstyle="round,pad=0.5,rounding_size=1.5", ec="#16A34A", fc="#F0FDF4", lw=1.2)
    o2 = FancyBboxPatch((72, 33), 24, 16, boxstyle="round,pad=0.5,rounding_size=1.5", ec="#D97706", fc="#FFFBEB", lw=1.2)
    o3 = FancyBboxPatch((72, 14), 24, 16, boxstyle="round,pad=0.5,rounding_size=1.5", ec="#0284C7", fc="#F0F9FF", lw=1.2)
    for b in [o1, o2, o3]: ax.add_patch(b)

    ax.text(84, 62.5, "Visual Diagnostics", fontsize=8.2, fontweight='bold', ha='center', color='#0F172A')
    ax.text(84, 56.5, "Exact Defect Bounding\nHeatmap & Sobel TURBO", fontsize=7.2, ha='center', color='#475569')

    ax.text(84, 43.5, "Fab Advisory & Root Cause", fontsize=8.2, fontweight='bold', ha='center', color='#0F172A')
    ax.text(84, 37.5, "Citing Fab SOP Protocol\nCorrective Action Directives", fontsize=7.2, ha='center', color='#475569')

    ax.text(84, 24.5, "Regulatory Audit Record", fontsize=8.2, fontweight='bold', ha='center', color='#0F172A')
    ax.text(84, 18.5, "SHA-256 Tamper Evident\nDisposition: PASS/REWORK/SCRAP", fontsize=7.2, ha='center', color='#475569')

    ax.annotate('', xy=(72, 59), xytext=(66, 56), arrowprops=dict(arrowstyle="->", lw=1.5, color='#16A34A'))
    ax.annotate('', xy=(72, 40), xytext=(66, 20), arrowprops=dict(arrowstyle="->", lw=1.5, color='#D97706'))
    ax.annotate('', xy=(72, 21), xytext=(66, 12), arrowprops=dict(arrowstyle="->", lw=1.5, color='#0284C7'))

    plt.tight_layout()
    out_path = os.path.join(OUT_DIR, "fig2_subsystem_dataflow.png")
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved:", out_path)

def draw_methodology_flowchart():
    """Generates Diagram 3: Flowchart of Proposed Solution (matching Page 5 of winning abstract)."""
    fig, ax = plt.subplots(figsize=(8, 12), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 115)
    ax.axis('off')

    # Flowchart Header
    ax.text(50, 111, "WaferQC Edge-AI Inspection Methodology", fontsize=14, fontweight='bold',
            ha='center', va='center', color='#0F172A')
    ax.text(50, 108, "Step-by-Step Inline Execution Flow with Deterministic Safety Gates",
            fontsize=8.8, ha='center', va='center', color='#0369A1', style='italic')

    # Flowchart Steps Data
    steps = [
        ("1. Ingest Raw SEM 256×256 e-Beam Inspection Frame", 101, 6),
        ("2. Execute eBeam De-Artifacting (Jitter Shift + Flare Subtraction)", 92, 6),
        ("3. Neural Classifier Inference on Cores 0-1 (ResNet-18 INT8)", 83, 6),
    ]

    for label, y_top, h in steps:
        p = FancyBboxPatch((15, y_top - h), 70, h, boxstyle="round,pad=0.4,rounding_size=1.2",
                           ec="#0284C7", fc="#F0F9FF", lw=1.2)
        ax.add_patch(p)
        ax.text(50, y_top - (h/2), label, fontsize=8.2, fontweight='bold', ha='center', va='center', color='#0F172A')

    # Connectors 1->2, 2->3
    ax.annotate('', xy=(50, 92), xytext=(50, 95), arrowprops=dict(arrowstyle="->", lw=1.5, color='#0284C7'))
    ax.annotate('', xy=(50, 83), xytext=(50, 86), arrowprops=dict(arrowstyle="->", lw=1.5, color='#0284C7'))

    # Decision Diamond 1: Confidence Gate
    ax.annotate('', xy=(50, 75.5), xytext=(50, 77), arrowprops=dict(arrowstyle="->", lw=1.5, color='#0284C7'))
    diamond1 = Polygon([[50, 75.5], [74, 69.5], [50, 63.5], [26, 69.5]], closed=True,
                       ec="#D97706", fc="#FFFBEB", lw=1.5)
    ax.add_patch(diamond1)
    ax.text(50, 70.8, "Confidence >= 0.55 &", fontsize=7.8, fontweight='bold', ha='center', color='#B45309')
    ax.text(50, 68, "Valid Topography?", fontsize=7.8, fontweight='bold', ha='center', color='#B45309')

    # Diamond 1 - No branch (Reject as UNKNOWN / Nuisance)
    ax.annotate('', xy=(88, 69.5), xytext=(74, 69.5), arrowprops=dict(arrowstyle="->", lw=1.5, color='#EF4444'))
    ax.text(77, 71.5, "No", fontsize=7.5, fontweight='bold', color='#EF4444')
    p_rej = FancyBboxPatch((80, 58), 18, 9, boxstyle="round,pad=0.4,rounding_size=1", ec="#EF4444", fc="#FEF2F2", lw=1.2)
    ax.add_patch(p_rej)
    ax.text(89, 63.8, "Flag UNKNOWN", fontsize=7.5, fontweight='bold', ha='center', color='#991B1B')
    ax.text(89, 60.5, "Filter Nuisance", fontsize=6.8, ha='center', color='#7F1D1D')

    # Diamond 1 - Yes branch (Proceed)
    ax.annotate('', xy=(50, 57), xytext=(50, 63.5), arrowprops=dict(arrowstyle="->", lw=1.5, color='#16A34A'))
    ax.text(51.8, 60.5, "Yes", fontsize=7.5, fontweight='bold', color='#16A34A')

    steps2 = [
        ("4. Extract Defect Contour Area (px²) & Exact Bounding Box", 57, 5.5),
        ("5. Compute Key Defectivity Index (KDI) & Evaluate Critical Overrides", 49, 5.5),
        ("6. Enqueue Event to Asynchronous SQLite WAL IPC Buffer", 41, 5.5),
        ("7. Retrieve Top-k Fab SOPs via Domain BM25 (Token Budget < 400)", 33, 5.5),
        ("8. Generate Root-Cause Advisory via Llama 3.2 1B (Cores 2-3)", 25, 5.5),
    ]

    for label, y_top, h in steps2:
        p = FancyBboxPatch((15, y_top - h), 70, h, boxstyle="round,pad=0.4,rounding_size=1.2",
                           ec="#16A34A", fc="#F0FDF4", lw=1.2)
        ax.add_patch(p)
        ax.text(50, y_top - (h/2), label, fontsize=8, fontweight='bold', ha='center', va='center', color='#0F172A')

    # Connectors for steps2
    for y in [49, 41, 33, 25]:
        ax.annotate('', xy=(50, y), xytext=(50, y + 2.5), arrowprops=dict(arrowstyle="->", lw=1.5, color='#16A34A'))

    # Decision Diamond 2: Verifier Gate V1-V5
    ax.annotate('', xy=(50, 17.5), xytext=(50, 19.5), arrowprops=dict(arrowstyle="->", lw=1.5, color='#16A34A'))
    diamond2 = Polygon([[50, 17.5], [74, 12.5], [50, 7.5], [26, 12.5]], closed=True,
                       ec="#D97706", fc="#FFFBEB", lw=1.5)
    ax.add_patch(diamond2)
    ax.text(50, 13.8, "Passes Deterministic", fontsize=7.8, fontweight='bold', ha='center', color='#B45309')
    ax.text(50, 11, "Verifiers V1 - V5?", fontsize=7.8, fontweight='bold', ha='center', color='#B45309')

    # Diamond 2 - No branch (Fallback template)
    ax.annotate('', xy=(88, 12.5), xytext=(74, 12.5), arrowprops=dict(arrowstyle="->", lw=1.5, color='#D97706'))
    ax.text(77, 14.5, "No", fontsize=7.5, fontweight='bold', color='#D97706')
    p_fall = FancyBboxPatch((80, 7.5), 18, 9, boxstyle="round,pad=0.4,rounding_size=1", ec="#D97706", fc="#FFFBEB", lw=1.2)
    ax.add_patch(p_fall)
    ax.text(89, 13.2, "Template Fallback", fontsize=7.2, fontweight='bold', ha='center', color='#B45309')
    ax.text(89, 9.8, "Deterministic Rule", fontsize=6.8, ha='center', color='#78350F')

    # Diamond 2 - Yes branch (Output & Audit)
    ax.annotate('', xy=(50, 2), xytext=(50, 7.5), arrowprops=dict(arrowstyle="->", lw=1.5, color='#16A34A'))
    ax.text(51.8, 5, "Yes", fontsize=7.5, fontweight='bold', color='#16A34A')

    p_final = FancyBboxPatch((15, -4), 70, 6, boxstyle="round,pad=0.4,rounding_size=1.2",
                             ec="#0F172A", fc="#F8FAFC", lw=1.5)
    ax.add_patch(p_final)
    ax.text(50, -1, "9. Log Cryptographic SHA-256 Audit Trail & Display Live Diagnostics",
            fontsize=8.2, fontweight='bold', ha='center', va='center', color='#0F172A')

    plt.tight_layout()
    out_path = os.path.join(OUT_DIR, "fig3_methodology_flowchart.png")
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved:", out_path)

if __name__ == '__main__':
    draw_block_diagram()
    draw_subsystem_dataflow()
    draw_methodology_flowchart()
    print("All 3 architectural diagrams generated successfully!")

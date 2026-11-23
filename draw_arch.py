"""
Generates a publication-grade architecture diagram for WaferQC using Matplotlib.
Saved as a high-resolution PNG to embed into the ReportLab PDF.
"""
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_architecture_diagram():
    out_dir = r"C:\Users\LENOVO\.gemini\antigravity\scratch\wafer_sem"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "waferqc_architecture.png")

    fig, ax = plt.subplots(figsize=(11, 6.2), dpi=300)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 6.2)
    ax.axis('off')

    # Styles
    navy = '#0B3C5D'
    teal = '#008080'
    light_blue = '#EAF2F8'
    light_teal = '#E0F2F1'
    light_orange = '#FFF3E0'
    light_gray = '#F8F9FA'
    border_color = '#333333'

    # 1. INPUT SOURCE
    box_input = patches.FancyBboxPatch((0.3, 4.4), 1.8, 1.3, boxstyle="round,pad=0.08", 
                                      fc='#F0F4F8', ec='#4A6572', lw=1.5)
    ax.add_patch(box_input)
    ax.text(1.2, 5.3, "INPUT SOURCE", ha='center', va='center', fontsize=9, fontweight='bold', color='#1D2731')
    ax.text(1.2, 4.8, "e-Beam Review\nStream or Replay\n(256px Crops)", ha='center', va='center', fontsize=7.5, color='#333333')

    # 2. PROCESS A - VISION WORKER
    box_proc_a = patches.FancyBboxPatch((2.5, 3.8), 8.2, 2.1, boxstyle="round,pad=0.1", 
                                        fc='#F4FBF7', ec='#2E7D32', lw=1.5, ls='--')
    ax.add_patch(box_proc_a)
    ax.text(6.6, 5.65, "PROCESS A — VISION WORKER (Pinned to Cores 0–1, ExecuTorch INT8)", 
            ha='center', va='center', fontsize=9, fontweight='bold', color='#1B5E20')

    # Sub-blocks inside Process A
    sub_a = [
        (2.7, "e-Beam De-Artifacting\n(Scan Jitter + Charging)\n< 4ms OpenCV", '#C8E6C9'),
        (5.3, "INT8 MobileNetV3 / YOLO\nExecuTorch XNNPACK\n< 10ms per die", '#A5D6A7'),
        (7.9, "Nuisance & Uncertainty\nAbstain Gate\n(Risk-Coverage Sweep)", '#C8E6C9')
    ]
    for x, text, col in sub_a:
        b = patches.FancyBboxPatch((x, 4.0), 2.3, 1.35, boxstyle="round,pad=0.06", fc=col, ec='#2E7D32', lw=1)
        ax.add_patch(b)
        ax.text(x + 1.15, 4.67, text, ha='center', va='center', fontsize=7.5, color='#1B5E20', multialignment='center')

    # Arrows in Process A
    ax.annotate('', xy=(5.3, 4.67), xytext=(5.0, 4.67), arrowprops=dict(arrowstyle="->", lw=1.5, color='#2E7D32'))
    ax.annotate('', xy=(7.9, 4.67), xytext=(7.6, 4.67), arrowprops=dict(arrowstyle="->", lw=1.5, color='#2E7D32'))
    # Arrow from Input to Process A
    ax.annotate('', xy=(2.7, 4.67), xytext=(2.1, 4.67), arrowprops=dict(arrowstyle="->", lw=1.5, color='#333333'))

    # 3. MAIN PROCESS - DECISION ENGINE
    box_proc_main = patches.FancyBboxPatch((0.3, 1.7), 4.8, 1.8, boxstyle="round,pad=0.1", 
                                          fc='#F0F4F8', ec='#0B3C5D', lw=1.5, ls='--')
    ax.add_patch(box_proc_main)
    ax.text(2.7, 3.25, "MAIN PROCESS — YIELD DECISION & SPC", 
            ha='center', va='center', fontsize=8.5, fontweight='bold', color='#0B3C5D')

    sub_m = [
        (0.5, "Killer Defect Index\n(KDI Noisy-OR)\nPass/Rework/Scrap", '#BBDEFB'),
        (2.0, "Instant Alert\nHardware / UI\n< 15ms latency", '#E3F2FD'),
        (3.5, "Spatial Wafer SPC\nEdge Ring vs Bullseye\nPoisson Clustered", '#BBDEFB')
    ]
    for x, text, col in sub_m:
        b = patches.FancyBboxPatch((x, 1.9), 1.35, 1.15, boxstyle="round,pad=0.05", fc=col, ec='#0B3C5D', lw=1)
        ax.add_patch(b)
        ax.text(x + 0.67, 2.47, text, ha='center', va='center', fontsize=6.8, color='#0B3C5D', multialignment='center')

    # 4. PROCESS B - ADVISOR WORKER
    box_proc_b = patches.FancyBboxPatch((5.6, 1.7), 5.1, 1.8, boxstyle="round,pad=0.1", 
                                        fc='#FFF8E1', ec='#E65100', lw=1.5, ls='--')
    ax.add_patch(box_proc_b)
    ax.text(8.15, 3.25, "PROCESS B — ADVISOR WORKER (Cores 2–3, ExecuTorch)", 
            ha='center', va='center', fontsize=8.5, fontweight='bold', color='#E65100')

    sub_b = [
        (5.8, "BM25 Fab SOP\nRetrieval Engine\n(Litho/Etch/CMP)", '#FFE082'),
        (7.4, "Llama 3.2 1B\nInstruct .pte\n8da4w XNNPACK", '#FFCC80'),
        (9.0, "Deterministic\nVerifier (V1-V5)\n+ Template Fallback", '#FFE082')
    ]
    for x, text, col in sub_b:
        b = patches.FancyBboxPatch((x, 1.9), 1.45, 1.15, boxstyle="round,pad=0.05", fc=col, ec='#E65100', lw=1)
        ax.add_patch(b)
        ax.text(x + 0.72, 2.47, text, ha='center', va='center', fontsize=6.8, color='#B71C1C', multialignment='center')

    # Inter-process Arrows
    # Process A -> Main Process
    ax.annotate('', xy=(2.7, 3.5), xytext=(9.0, 4.0),
                arrowprops=dict(arrowstyle="->", lw=1.5, color='#2E7D32', connectionstyle="arc3,rad=-0.15"))
    ax.text(6.0, 3.65, "Verified Die Detections (IPC Queue)", fontsize=7, color='#2E7D32', ha='center', backgroundcolor='#ffffff')

    # Main Process -> Advisor Process
    ax.annotate('', xy=(5.8, 2.5), xytext=(4.85, 2.5),
                arrowprops=dict(arrowstyle="->", lw=1.5, color='#E65100'))
    ax.text(5.32, 2.65, "Event Trigger", fontsize=7, color='#E65100', ha='center')

    # 5. BOTTOM TIER: GOVERNOR, AUDIT LOG, LOCAL DASHBOARD
    sub_bottom = [
        (0.5, 0.2, 2.5, 1.1, "THERMAL GOVERNOR\nvcgencmd + queue depth\nFULL / BALANCED / FAST", '#ECEFF1', '#37474F'),
        (3.8, 0.2, 3.3, 1.1, "SQLite (WAL) AUDIT LOG\nSHA-256 Hashes | Die X,Y | KDI\nLlama Advice | Replay from Log", '#ECEFF1', '#37474F'),
        (7.9, 0.2, 2.7, 1.1, "LOCAL OFFLINE DASHBOARD\nFastAPI + SSE Stream\nInteractive 300mm Wafer Map", '#ECEFF1', '#37474F')
    ]
    for x, y, w, h, text, col, border in sub_bottom:
        b = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06", fc=col, ec=border, lw=1.2)
        ax.add_patch(b)
        ax.text(x + w/2, y + h/2, text, ha='center', va='center', fontsize=7.2, color='#263238', multialignment='center')

    # Arrows to bottom
    ax.annotate('', xy=(1.75, 1.3), xytext=(1.75, 1.7), arrowprops=dict(arrowstyle="<->", lw=1.2, color='#37474F'))
    ax.annotate('', xy=(5.45, 1.3), xytext=(3.5, 1.7), arrowprops=dict(arrowstyle="->", lw=1.2, color='#37474F'))
    ax.annotate('', xy=(5.45, 1.3), xytext=(7.4, 1.7), arrowprops=dict(arrowstyle="->", lw=1.2, color='#37474F'))
    ax.annotate('', xy=(9.2, 1.3), xytext=(6.5, 0.75), arrowprops=dict(arrowstyle="<->", lw=1.2, color='#37474F'))

    plt.tight_layout()
    plt.savefig(out_path, bbox_inches='tight', dpi=300)
    plt.close()
    print("Architecture diagram successfully generated at:", out_path)

if __name__ == "__main__":
    draw_architecture_diagram()

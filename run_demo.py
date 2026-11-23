"""
WaferQC Interactive Replay Demo Runner
Processes an automated batch of test SEM defect crops through the full inspection pipeline,
logs results to SQLite, and compiles a comprehensive standalone HTML report.
"""
import os
import glob
import time
import base64
import argparse
import cv2
from waferqc.pipeline import WaferQCPipeline

def encode_img_base64(img_path, bbox=None):
    img = cv2.imread(img_path)
    if img is None:
        return ""
    if bbox:
        x1, y1, x2, y2 = bbox
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
    _, buffer = cv2.imencode(".png", img)
    return base64.b64encode(buffer).decode("utf-8")

def run_demo(test_dir="dataset_3k/test", count=24, delay=0.1):
    print("=" * 80)
    print("WAFERQC REAL-TIME ON-DEVICE INSPECTION REPLAY DEMO")
    print("Bharat AI-SoC Challenge 2026-27 | Target: Raspberry Pi 5")
    print("=" * 80)

    pipe = WaferQCPipeline(
        model_path="outputs/best_model.pth",
        sop_dir="data/sop_knowledge_base",
        db_path="waferqc_audit.db"
    )

    # Gather balanced sample images across test classes
    classes = ["bridge", "particle", "scratch", "clean", "nuisance_charging", "nuisance_jitter"]
    sample_files = []
    per_class = max(1, count // len(classes))
    for c in classes:
        c_files = sorted(glob.glob(os.path.join(test_dir, c, "*.png")))
        sample_files.extend(c_files[:per_class])

    print(f"Selected {len(sample_files)} test images for automated inspection run.")
    print("-" * 80)
    print(f"{'#':<4}{'True Class':<18}{'Pred Class':<18}{'Conf':<8}{'KDI':<8}{'Disp':<10}{'Time(ms)':<10}")
    print("-" * 80)

    results = []
    for idx, fpath in enumerate(sample_files, start=1):
        true_cls = os.path.basename(os.path.dirname(fpath))
        ptype = "contact_matrix" if "contact" in fpath else "line_space"

        res = pipe.process_image(fpath, pattern_type=ptype)
        res["true_class"] = true_cls
        res["b64_thumb"] = encode_img_base64(fpath, res["bbox"])
        results.append(res)

        print(f"{idx:<4}{true_cls:<18}{res['predicted_class']:<18}"
              f"{res['confidence']:<8.2f}{res['kdi_score']:<8.3f}"
              f"{res['disposition']:<10}{res['timing_ms']['total']:<10.1f}")
        time.sleep(delay)

    print("-" * 80)
    print("Inspection Run Finished. Compiling Standalone HTML Demo Report...")

    # Build standalone HTML report
    html_out = "outputs/demo_report.html"
    generate_html_report(results, html_out)
    print(f"Report successfully generated at: {html_out}")
    print("=" * 80)

def generate_html_report(results, out_path):
    rows_html = []
    for r in results:
        disp_class = r["disposition"].lower()
        adv = r.get("advisor", {})
        adv_text = adv.get("analysis", "") if isinstance(adv, dict) else str(adv)
        sop_cited = ", ".join(adv.get("cited_sop_ids", [])) if isinstance(adv, dict) else ""

        row = f"""
        <tr>
          <td><img src="data:image/png;base64,{r['b64_thumb']}" width="96" height="96" style="border-radius:4px; border:1px solid #334155;"></td>
          <td><strong>{r['true_class']}</strong></td>
          <td><span style="color:#38bdf8; font-weight:bold;">{r['predicted_class']}</span> ({r['confidence']*100:.1f}%)</td>
          <td><code>{r['kdi_score']:.3f}</code></td>
          <td><span class="badge badge-{disp_class}">{r['disposition']}</span></td>
          <td>{r['area_px']} px</td>
          <td>{r['timing_ms']['total']:.1f} ms</td>
          <td style="font-size:0.8rem; color:#cbd5e1;">
            <div>{adv_text}</div>
            <div style="color:#94a3b8; margin-top:4px;"><em>Cited: {sop_cited or 'None'} | Source: {r['advisor_source']}</em></div>
          </td>
        </tr>
        """
        rows_html.append(row)

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>WaferQC Automated Replay Inspection Report</title>
      <style>
        body {{ background: #0b0f19; color: #f1f5f9; font-family: system-ui, sans-serif; padding: 24px; }}
        h1 {{ color: #38bdf8; font-size: 1.5rem; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 10px; border-bottom: 1px solid #1e293b; text-align: left; vertical-align: middle; }}
        th {{ color: #94a3b8; font-size: 0.85rem; text-transform: uppercase; }}
        .badge {{ padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.75rem; text-transform: uppercase; }}
        .badge-pass {{ background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid #10b981; }}
        .badge-rework {{ background: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid #f59e0b; }}
        .badge-scrap {{ background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid #ef4444; }}
      </style>
    </head>
    <body>
      <h1>WaferQC Automated SEM Defect Inspection Report</h1>
      <p style="color: #94a3b8;">Bharat AI-SoC Challenge 2026-27 | Target Hardware: Raspberry Pi 5 (8GB) | Processed: {len(results)} SEM crops</p>
      <table>
        <thead>
          <tr>
            <th>Crop</th>
            <th>True Class</th>
            <th>Prediction</th>
            <th>KDI</th>
            <th>Disposition</th>
            <th>Area</th>
            <th>Latency</th>
            <th>Advisory & SOP Grounding</th>
          </tr>
        </thead>
        <tbody>
          {"".join(rows_html)}
        </tbody>
      </table>
    </body>
    </html>
    """
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(full_html)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-dir", type=str, default="dataset_3k/test")
    parser.add_argument("--count", type=int, default=24)
    parser.add_argument("--delay", type=float, default=0.05)
    args = parser.parse_args()

    run_demo(test_dir=args.test_dir, count=args.count, delay=args.delay)

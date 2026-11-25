"""
Comprehensive Verification of ALL WaferQC Operations & Visual Overlays.
Checks every API endpoint, all 6 defect/nuisance classes, SOP grounding,
legacy/uploaded localization, and renders an image grid for visual inspection.
"""
import os
import base64
import requests
import cv2
import numpy as np

BASE = "http://127.0.0.1:8000"


def decode_b64_img(data_url: str) -> np.ndarray:
    header, b64 = data_url.split(",", 1)
    arr = np.frombuffer(base64.b64decode(b64), np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def main():
    print("=" * 80)
    print("WAFERQC FULL-STACK VERIFICATION ACROSS ALL OPERATIONS & CLASSES")
    print("=" * 80)

    # 1. Core GET endpoints
    for ep in ["/", "/api/summary", "/api/events", "/api/queue", "/api/model/info", "/api/sops", "/api/export_csv"]:
        r = requests.get(BASE + ep, timeout=15)
        assert r.status_code == 200, f"GET {ep} returned {r.status_code}"
    sops = requests.get(BASE + "/api/sops").json()
    print(f"[PASS] All 7 core API endpoints HTTP 200 | SOP count = {len(sops)}")

    # Static plots check
    for img_ep in ["/outputs/confusion_matrix.png", "/outputs/threshold_sweep.png", "/outputs/training_curves.png"]:
        r = requests.get(BASE + img_ep, timeout=10)
        assert r.status_code == 200, f"Static {img_ep} returned {r.status_code}"
    print("[PASS] All 3 diagnostic plots served via /outputs/")

    # 2. Test all 6 classes (Sample Preview -> Inspect Sample)
    expected_sop_prefixes = {
        "bridge": ("SOP-LIT",),
        "particle": ("SOP-CLN", "SOP-DEP"),
        "scratch": ("SOP-CMP", "SOP-HND", "SOP-CLN"),
        "clean": ("SOP-NOM",),
        "nuisance_charging": ("SOP-SEM",),
        "nuisance_jitter": ("SOP-SEM",),
    }

    montage_rows = []
    for cls in ["bridge", "particle", "scratch", "clean", "nuisance_charging", "nuisance_jitter"]:
        # Load sample preview
        r1 = requests.get(f"{BASE}/api/sample_image?class_name={cls}", timeout=10)
        assert r1.status_code == 200
        samp = r1.json()
        path = samp["image_path"]

        # Run pipeline on exact loaded sample
        r2 = requests.post(f"{BASE}/api/inspect_sample", data={"image_path": path, "pattern_type": "line_space"}, timeout=20)
        assert r2.status_code == 200
        res = r2.json()

        pred = res["predicted_class"]
        conf = res["confidence"]
        disp = res["disposition"]
        bbox = res["bbox"]
        area = res["area_px"]
        sids = res["advisor"].get("cited_sop_ids", [])
        titles = res["advisor"].get("cited_sop_titles", [])
        rc = res["advisor"].get("root_cause_hypothesis", "")

        print(f"\n[{cls.upper()}] Sample: {samp['filename']}")
        print(f"  Pred={pred} ({conf:.2%}) | Disp={disp} | KDI={res['kdi_score']:.3f} | BBox={bbox} | Area={area} px")
        print(f"  SOP={titles or sids}")
        print(f"  RootCause={rc[:90]}")

        assert pred == cls, f"Expected {cls}, got {pred} on {samp['filename']}"
        if cls in ("bridge", "particle", "scratch"):
            assert bbox is not None, f"Missing bbox for {cls}"
            assert disp in ("REWORK", "SCRAP"), f"Unexpected disp {disp} for {cls}"
        else:
            assert bbox is None, f"Unexpected bbox {bbox} for {cls}"
            assert disp == "PASS", f"Unexpected disp {disp} for {cls}"

        assert sids and sids[0].startswith(expected_sop_prefixes[cls]), f"Wrong SOP {sids} for {cls}"

        # Collect visuals for montage (Raw | Overlay | Heatmap)
        raw_img = decode_b64_img(res["visuals"]["raw"])
        ov_img = decode_b64_img(res["visuals"]["overlay"])
        hm_img = decode_b64_img(res["visuals"]["heatmap"])
        row_img = np.hstack([raw_img, ov_img, hm_img])
        montage_rows.append(row_img)

    # 3. Test legacy / upload localization (not in metadata.csv)
    print("\n--- Testing Non-Metadata / Uploaded Image Localization ---")
    for legacy_path, exp_cls in [
        ("dataset_3k/test/bridge/SEM_TE_00107_bridge.png", "bridge"),
        ("dataset_3k/test/particle/SEM_TE_00109_particle.png", "particle"),
        ("dataset_3k/test/scratch/SEM_TE_00112_scratch.png", "scratch"),
    ]:
        with open(legacy_path, "rb") as f:
            r_up = requests.post(
                f"{BASE}/api/inspect",
                files={"file": (f"custom_{os.path.basename(legacy_path)}", f, "image/png")},
                data={"pattern_type": "contact_matrix"},
                timeout=20
            )
        assert r_up.status_code == 200
        res_u = r_up.json()
        print(f"  Upload {os.path.basename(legacy_path)} -> Pred={res_u['predicted_class']} ({res_u['confidence']:.2%}), BBox={res_u['bbox']}, Area={res_u['area_px']}")
        assert res_u["predicted_class"] == exp_cls
        assert res_u["bbox"] is not None
        raw_img = decode_b64_img(res_u["visuals"]["raw"])
        ov_img = decode_b64_img(res_u["visuals"]["overlay"])
        hm_img = decode_b64_img(res_u["visuals"]["heatmap"])
        montage_rows.append(np.hstack([raw_img, ov_img, hm_img]))

    # Save montage to inspect visually
    montage = np.vstack(montage_rows)
    out_montage = r"E:\WaferQC\outputs\verify_all_overlays.png"
    cv2.imwrite(out_montage, montage)
    print(f"\n[PASS] Saved visual montage to {out_montage}")
    print("=" * 80)
    print("ALL OPERATIONS, ALL 6 CLASSES, UPLOADS, AND SOPS VERIFIED 100%!")
    print("=" * 80)


if __name__ == "__main__":
    main()

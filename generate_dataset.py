"""
WaferQC Batch Dataset Generator (Phase 1) - patched
Generates structured train / val / test splits with balanced classes,
metadata CSVs, and domain-randomized SEM review crops.
"""

import os
import argparse
import csv
import random
import cv2
import numpy as np
from tqdm import tqdm
from sem_generator_v2 import generate_sample_v2

def generate_wafer_dataset(out_root, num_samples=3000, seed=42):
    n_train = int(num_samples * 0.70)
    n_val = int(num_samples * 0.15)
    splits = {"train": n_train, "val": n_val, "test": num_samples - n_train - n_val}  # PATCH: no lost samples

    classes = ["clean", "bridge", "particle", "scratch", "nuisance_charging", "nuisance_jitter"]

    os.makedirs(out_root, exist_ok=True)
    meta_path = os.path.join(out_root, "metadata.csv")

    print(f"Generating {num_samples} SEM samples into: {out_root}")
    print(f"Splits: Train={splits['train']}, Val={splits['val']}, Test={splits['test']}")
    print(f"Classes: {classes}")

    with open(meta_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # PATCH: seed column added so any sample can be regenerated
        writer.writerow(["sample_id", "split", "label", "pattern_type", "bbox_x1", "bbox_y1", "bbox_x2", "bbox_y2", "area_px", "seed", "filepath"])

        sample_idx = 0
        for split_name, split_count in splits.items():
            per_class = split_count // len(classes)
            for c_idx, label in enumerate(classes):
                class_dir = os.path.join(out_root, split_name, label)
                os.makedirs(class_dir, exist_ok=True)

                count = per_class if c_idx < len(classes) - 1 else (split_count - per_class * (len(classes) - 1))

                for i in tqdm(range(count), desc=f"{split_name}/{label}", leave=False):
                    sample_idx += 1
                    sid = f"SEM_{split_name[:2].upper()}_{sample_idx:05d}"
                    ptype = "line_space" if (i % 2 == 0) else "contact_matrix"

                    # PATCH: the generator uses BOTH Python's random and NumPy's RNG
                    s = seed + sample_idx
                    random.seed(s)
                    np.random.seed(s)

                    if label == "nuisance_charging":
                        # PATCH: strong charging flare, no defect (was identical to "clean")
                        img, _, bbox, mask = generate_sample_v2(defect_type="clean", pattern_type=ptype, artifact="charging")
                        bbox = None
                        area = 0
                    elif label == "nuisance_jitter":
                        # PATCH: strong scan-line jitter, no defect
                        img, _, bbox, mask = generate_sample_v2(defect_type="clean", pattern_type=ptype, artifact="jitter")
                        bbox = None
                        area = 0
                    else:
                        img, _, bbox, mask = generate_sample_v2(defect_type=label, pattern_type=ptype)
                        area = int(np.sum(mask > 0)) if mask is not None else 0
                        if label != "clean":
                            assert bbox is not None and area > 0, f"empty defect {sid}"  # PATCH

                    fname = f"{sid}_{label}.png"
                    fpath = os.path.join(class_dir, fname)
                    assert img.dtype == np.uint8 and cv2.imwrite(fpath, img), f"write failed: {fpath}"  # PATCH

                    b_str = [str(x) for x in bbox] if bbox is not None else ["", "", "", ""]  # PATCH
                    rel_path = os.path.relpath(fpath, out_root).replace("\\", "/")  # PATCH: portable paths
                    writer.writerow([sid, split_name, label, ptype, b_str[0], b_str[1], b_str[2], b_str[3], area, s, rel_path])

    print(f"Dataset generation complete! Metadata saved to {meta_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=str, default="dataset_3k")  # PATCH: relative default
    parser.add_argument("--num-samples", type=int, default=3000)
    parser.add_argument("--seed", type=int, default=42)  # PATCH
    args = parser.parse_args()

    generate_wafer_dataset(args.out_dir, num_samples=args.num_samples, seed=args.seed)

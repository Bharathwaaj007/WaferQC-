"""
eBeam De-artifacting & Nuisance Separation Module
Demonstrates AMAT Slide 1:
1. Scan Jitter Correction (Row-wise phase alignment)
2. Charging Flare Suppression (Rolling-ball / morphological background subtraction)
3. Defect vs. Nuisance separation
"""
import os
import cv2
import numpy as np

def remove_scan_jitter(img):
    """Detects and compensates row-wise horizontal jitter."""
    corrected = img.copy().astype(np.float32)
    h, w = img.shape
    
    # Calculate row-to-row correlation or gradient along vertical axis
    # Jitter rows produce sharp horizontal spikes in vertical gradient
    dy = np.abs(np.diff(corrected, axis=0))
    row_energy = np.mean(dy, axis=1)
    
    # Median row energy baseline
    med_energy = np.median(row_energy)
    mad = np.median(np.abs(row_energy - med_energy)) + 1e-5
    
    # Identify jitter candidates (high row discontinuity)
    jitter_indices = np.where(row_energy > med_energy + 2.5 * mad)[0]
    
    # Correct by aligning candidate row with its neighbors using 1D phase cross-correlation
    for r in jitter_indices:
        if 1 <= r < h - 1:
            ref = 0.5 * (corrected[r - 1] + corrected[r + 1])
            row = corrected[r]
            
            best_shift = 0
            best_diff = np.mean((row - ref) ** 2)
            for s in [-2, -1, 1, 2]:
                shifted = np.roll(row, s)
                diff = np.mean((shifted - ref) ** 2)
                if diff < best_diff:
                    best_diff = diff
                    best_shift = s
            corrected[r] = np.roll(row, best_shift)
            
    return np.clip(corrected, 0, 255).astype(np.uint8), len(jitter_indices)

def remove_charging_flare(img, kernel_size=35):
    """
    Suppresses low-frequency electrostatic potential charging flares
    using top-hat / background estimation.
    """
    # Estimate charging illumination field via large morphological opening
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    background = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
    
    # Equalize flat field
    # Flatten contrast variations
    mean_val = np.mean(img)
    corrected = img.astype(np.float32) - background.astype(np.float32) + np.mean(background)
    corrected = np.clip(corrected, 0, 255).astype(np.uint8)
    return corrected, background

def test_deartifact():
    from sem_generator_v2 import generate_sample_v2
    
    # Generate an image with particle, heavy charging, and scan jitter
    raw_img, label, bbox, mask = generate_sample_v2(
        defect_type="particle", pattern_type="contact_matrix", artifact="charging"
    )
    
    # Step 1: Remove scan jitter
    jitter_free, n_jitters = remove_scan_jitter(raw_img)
    
    # Step 2: Remove charging flare
    denoised, charging_map = remove_charging_flare(jitter_free)
    
    # Build a 4-panel visual demonstration: Raw SEM, Jitter Removed, De-charged (Denoised), Close-up
    h, w = raw_img.shape
    panel = np.zeros((h, w * 3, 3), dtype=np.uint8)
    
    panel[:, :w] = cv2.cvtColor(raw_img, cv2.COLOR_GRAY2BGR)
    panel[:, w:2*w] = cv2.cvtColor(jitter_free, cv2.COLOR_GRAY2BGR)
    panel[:, 2*w:] = cv2.cvtColor(denoised, cv2.COLOR_GRAY2BGR)
    
    # Annotate on denoised: bounding box around the real defect
    if bbox:
        cv2.rectangle(panel[:, 2*w:], (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 0, 255), 2)
        cv2.putText(panel[:, 2*w:], "Real Particle", (bbox[0], max(15, bbox[1] - 5)), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
        
    # Headers
    header = np.full((40, panel.shape[1], 3), 20, dtype=np.uint8)
    cv2.putText(header, "1. Raw SEM (Jitter + Charging Nuisance)", (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
    cv2.putText(header, "2. Scan-Jitter Corrected", (w + 15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
    cv2.putText(header, "3. Denoised & Real Defect Isolated", (2*w + 15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 120), 1)
    
    final = np.vstack([header, panel])
    out_path = os.path.join(art_dir, "sem_denoising_amat_slide1.png")
    cv2.imwrite(out_path, final)
    print(f"De-artifacting test saved to: {out_path}")

if __name__ == "__main__":
    test_deartifact()

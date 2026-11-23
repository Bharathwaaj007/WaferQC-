import os
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(project_root)
sys.path.insert(0, project_root)

import cv2
import numpy as np
import pandas as pd

# Load metadata
df = pd.read_csv("dataset_3k/metadata.csv")
meta_lookup = {}
for _, row in df.iterrows():
    # Key by basename
    bn = os.path.basename(str(row['filepath']))
    meta_lookup[bn] = {
        'bbox': (int(row['bbox_x1']), int(row['bbox_y1']), int(row['bbox_x2']), int(row['bbox_y2'])) if pd.notna(row['bbox_x1']) else None,
        'area_px': int(row['area_px']) if pd.notna(row['area_px']) else 0,
        'label': row['label'],
        'pattern_type': row['pattern_type']
    }

def generate_visual_diagnostics(img_gray, pred_class, bbox=None, area_px=0):
    H, W = img_gray.shape
    
    # 1. Base BGR image
    bgr = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2BGR)
    
    # 2. Defect Heatmap (Difference / Anomaly)
    blurred = cv2.GaussianBlur(img_gray, (15, 15), 0)
    diff = cv2.absdiff(img_gray, blurred)
    norm_diff = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX)
    heatmap = cv2.applyColorMap(norm_diff, cv2.COLORMAP_JET)
    
    # 3. Sobel Gradient Magnitude (like fracture Sobel)
    sobelx = cv2.Sobel(img_gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(img_gray, cv2.CV_64F, 0, 1, ksize=3)
    grad_mag = np.sqrt(sobelx**2 + sobely**2)
    grad_norm = cv2.normalize(grad_mag, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    sobel_colored = cv2.applyColorMap(grad_norm, cv2.COLORMAP_TURBO)
    
    # 4. Overlay with EXACT Rounding / Bounding Box & Target Callout
    overlay = bgr.copy()
    
    if bbox is not None and pred_class not in ('clean', 'nuisance_charging', 'nuisance_jitter'):
        x1, y1, x2, y2 = bbox
        # Pad slightly for visual clearance
        pad = 6
        x1 = max(0, x1 - pad)
        y1 = max(0, y1 - pad)
        x2 = min(W - 1, x2 + pad)
        y2 = min(H - 1, y2 + pad)
        
        # Color based on class
        box_color = (68, 68, 239) if pred_class in ('bridge', 'scratch') else (11, 158, 245) # BGR
        
        # Draw rounded rectangle (or smooth corner box)
        radius = 8
        # Corners
        cv2.rectangle(overlay, (x1 + radius, y1), (x2 - radius, y2), box_color, 2)
        cv2.rectangle(overlay, (x1, y1 + radius), (x2, y2 - radius), box_color, 2)
        cv2.circle(overlay, (x1 + radius, y1 + radius), radius, box_color, 2)
        cv2.circle(overlay, (x2 - radius, y1 + radius), radius, box_color, 2)
        cv2.circle(overlay, (x1 + radius, y2 - radius), radius, box_color, 2)
        cv2.circle(overlay, (x2 - radius, y2 - radius), radius, box_color, 2)
        
        # Center crosshair target
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        cv2.drawMarker(overlay, (cx, cy), box_color, cv2.MARKER_CROSS, 14, 2)
        
        # Tag banner above box
        tag_text = f"{pred_class.upper()} [{area_px} px]"
        (tw, th), _ = cv2.getTextSize(tag_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        tag_y1 = max(0, y1 - th - 8)
        tag_y2 = y1
        cv2.rectangle(overlay, (x1, tag_y1), (x1 + tw + 10, tag_y2), box_color, -1)
        cv2.putText(overlay, tag_text, (x1 + 5, tag_y2 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
        
        # Also highlight defect zone inside heatmap
        cv2.rectangle(heatmap, (x1, y1), (x2, y2), (255, 255, 255), 2)
    elif pred_class == 'clean':
        # Green nominal checkmark banner
        cv2.putText(overlay, "NOMINAL TOPOGRAPHY - NO DEFECT DETECTED", (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 230, 115), 1, cv2.LINE_AA)
        
    os.makedirs("outputs/test_visuals", exist_ok=True)
    cv2.imwrite("outputs/test_visuals/overlay.png", overlay)
    cv2.imwrite("outputs/test_visuals/heatmap.png", heatmap)
    cv2.imwrite("outputs/test_visuals/sobel.png", sobel_colored)
    print("Diagnostics written successfully to outputs/test_visuals/")

# Test on a test bridge sample
test_img = cv2.imread("dataset_3k/test/bridge/SEM_TE_02626_bridge.png", cv2.IMREAD_GRAYSCALE)
meta = meta_lookup.get("SEM_TE_02626_bridge.png")
print("Meta found:", meta)
generate_visual_diagnostics(test_img, "bridge", meta['bbox'], meta['area_px'])

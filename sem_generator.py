"""
SEM Wafer Defect & Nuisance Synthesizer
Based on Applied Materials (AMAT) eBeam Metrology & Defect Review principles.
Simulates:
  - Nanoscale patterned layouts: Line/Space arrays, Capsule/Contact hole matrices
  - Physical Defect Injection: Bridge (electrical short), Particle (contamination), Scratch (CMP abrasion)
  - SEM Imaging Physics: Secondary electron edge blooming, Poisson shot noise, Beam blur
  - Fab Nuisance Artifacts: e-beam scan jitter, Dielectric surface charging gradients
"""

import os
import random
import numpy as np
import cv2
from scipy.ndimage import gaussian_filter

def create_line_space_layout(img_size=256, pitch=24, line_width=12, angle_deg=45):
    """Generates a periodic line-space array at a specified angle."""
    x = np.arange(img_size)
    y = np.arange(img_size)
    xx, yy = np.meshgrid(x, y)
    
    rad = np.deg2rad(angle_deg)
    # Coordinate along the perpendicular direction to lines
    u = xx * np.cos(rad) + yy * np.sin(rad)
    phase = np.mod(u, pitch)
    
    # 1.0 on lines, 0.0 in trenches
    layout = np.where(phase < line_width, 1.0, 0.0).astype(np.float32)
    return layout

def create_dram_capsule_layout(img_size=256, pitch_x=32, pitch_y=24, cap_w=18, cap_h=8, angle_deg=45):
    """Generates a staggered stadium/capsule layout similar to DRAM active areas (Slide 2)."""
    # Create an over-sized grid and rotate
    pad = int(img_size * 0.5)
    total_size = img_size + 2 * pad
    base = np.zeros((total_size, total_size), dtype=np.float32)
    
    for row_idx, y in enumerate(range(20, total_size - 20, pitch_y)):
        x_offset = (row_idx % 2) * (pitch_x // 2)
        for x in range(20, total_size - 20, pitch_x):
            cx = x + x_offset
            cy = y
            # Draw stadium / rounded rectangle
            cv2.ellipse(base, (cx, cy), (cap_w // 2, cap_h // 2), 0, 0, 360, 1.0, -1)
            
    # Rotate by angle
    M = cv2.getRotationMatrix2D((total_size // 2, total_size // 2), angle_deg, 1.0)
    rotated = cv2.warpAffine(base, M, (total_size, total_size))
    # Crop center
    layout = rotated[pad:pad + img_size, pad:pad + img_size]
    return np.clip(layout, 0.0, 1.0)

def inject_bridge_defect(layout):
    """Injects an electrical bridge short between adjacent structures."""
    img_size = layout.shape[0]
    mask = np.zeros_like(layout)
    
    # Find two distinct high regions that are separated by a trench (0)
    # Pick a random center in the middle 60% of the image
    cx = random.randint(int(img_size * 0.25), int(img_size * 0.75))
    cy = random.randint(int(img_size * 0.25), int(img_size * 0.75))
    
    bridge_len = random.randint(12, 22)
    bridge_w = random.randint(4, 8)
    angle = random.uniform(0, 180)
    
    # Draw bridge connection
    rad = np.deg2rad(angle)
    dx = int(bridge_len * np.cos(rad) / 2)
    dy = int(bridge_len * np.sin(rad) / 2)
    pt1 = (cx - dx, cy - dy)
    pt2 = (cx + dx, cy + dy)
    
    cv2.line(mask, pt1, pt2, 1.0, bridge_w)
    # Organic distortion
    noise = np.random.normal(0, 0.1, mask.shape)
    mask = gaussian_filter(mask + noise, sigma=1.0)
    mask = np.where(mask > 0.35, 1.0, 0.0).astype(np.float32)
    
    defective_layout = np.clip(layout + mask, 0.0, 1.0)
    
    # Calculate bounding box
    ys, xs = np.where(mask > 0)
    if len(xs) > 0:
        bbox = (int(np.min(xs)), int(np.min(ys)), int(np.max(xs)), int(np.max(ys)))
    else:
        bbox = (cx - 10, cy - 10, cx + 10, cy + 10)
        
    return defective_layout, mask, bbox, "bridge"

def inject_particle_defect(layout):
    """Injects a 3D foreign contamination particle with high topography."""
    img_size = layout.shape[0]
    mask = np.zeros_like(layout)
    
    cx = random.randint(int(img_size * 0.2), int(img_size * 0.8))
    cy = random.randint(int(img_size * 0.2), int(img_size * 0.8))
    radius = random.randint(8, 20)
    
    # Irregular particle shape using overlapping circles
    for _ in range(4):
        ox = random.randint(-radius // 3, radius // 3)
        oy = random.randint(-radius // 3, radius // 3)
        r = random.randint(int(radius * 0.7), radius)
        cv2.circle(mask, (cx + ox, cy + oy), r, 1.0, -1)
        
    mask = gaussian_filter(mask, sigma=1.2)
    particle_topography = np.clip(mask * random.uniform(1.2, 1.8), 0.0, 2.0)
    
    # Particle overlays and obscures underlying pattern
    defective_layout = np.where(mask > 0.2, particle_topography, layout)
    
    ys, xs = np.where(mask > 0.2)
    bbox = (int(np.min(xs)), int(np.min(ys)), int(np.max(xs)), int(np.max(ys)))
    return defective_layout, (mask > 0.2).astype(np.float32), bbox, "particle"

def inject_scratch_defect(layout):
    """Injects a CMP abrasive micro-scratch cutting across traces."""
    img_size = layout.shape[0]
    mask = np.zeros_like(layout)
    
    # Start and end points traversing a large portion
    x1 = random.randint(20, img_size // 3)
    y1 = random.randint(20, img_size - 20)
    x2 = random.randint(2 * img_size // 3, img_size - 20)
    y2 = random.randint(20, img_size - 20)
    
    scratch_w = random.randint(3, 7)
    
    # Jagged scratch line
    pts = []
    num_pts = 6
    for i in range(num_pts):
        t = i / (num_pts - 1)
        xi = int(x1 + t * (x2 - x1) + random.randint(-4, 4))
        yi = int(y1 + t * (y2 - y1) + random.randint(-4, 4))
        pts.append((xi, yi))
        
    for i in range(len(pts) - 1):
        cv2.line(mask, pts[i], pts[i + 1], 1.0, scratch_w)
        
    # Scratch digs into the material (destroys line traces)
    defective_layout = np.where(mask > 0.5, 0.05, layout)
    
    # Displaced material pile-up at scratch edges (bright lip)
    edge_lip = cv2.dilate(mask, np.ones((3, 3), np.uint8)) - mask
    defective_layout = np.clip(defective_layout + edge_lip * 0.6, 0.0, 1.5)
    
    ys, xs = np.where(mask > 0.5)
    bbox = (int(np.min(xs)), int(np.min(ys)), int(np.max(xs)), int(np.max(ys)))
    return defective_layout, (mask > 0.5).astype(np.float32), bbox, "scratch"

def apply_sem_physics(layout, edge_bloom_strength=1.8, beam_blur_sigma=1.1, shot_noise_factor=0.08):
    """
    Simulates Scanning Electron Microscopy (SEM) physics:
    - Secondary Electron (SE) emission: Edge blooming (I_se ~ sec(theta))
    - Beam point spread function (PSF) blur
    - Low-dose Poisson shot noise & detector noise
    """
    # 1. Base material contrast (trenches dark ~0.2, top surface ~0.65)
    sem_base = layout * 0.5 + 0.2
    
    # 2. Secondary electron edge blooming: gradient magnitude
    gx = cv2.Sobel(layout, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(layout, cv2.CV_32F, 0, 1, ksize=3)
    grad = np.sqrt(gx**2 + gy**2)
    # Bright blooming on edges
    edge_bloom = cv2.GaussianBlur(grad, (3, 3), 0.8) * edge_bloom_strength * 0.25
    
    sem_img = sem_base + edge_bloom
    
    # 3. Beam PSF blur (finite spot size)
    sem_img = gaussian_filter(sem_img, sigma=beam_blur_sigma)
    
    # 4. Poisson shot noise (simulates discrete electron hits)
    # Scale to simulated electron count (e.g., ~150-300 electrons/pixel)
    dose = 250.0
    electron_counts = np.random.poisson(np.clip(sem_img * dose, 1.0, None))
    sem_noisy = electron_counts / dose
    
    # 5. Detector thermal / Gaussian noise
    detector_noise = np.random.normal(0, shot_noise_factor, sem_img.shape)
    final_sem = sem_noisy + detector_noise
    
    return np.clip(final_sem, 0.0, 1.0)

def apply_nuisance_scan_jitter(img, jitter_prob=0.12, max_shift=2):
    """
    Simulates e-beam column scan jitter (Slide 1):
    Horizontal line scan micro-displacements.
    """
    h, w = img.shape
    jittered = img.copy()
    num_jitters = random.randint(3, 7)
    
    jitter_rows = []
    for _ in range(num_jitters):
        y = random.randint(10, h - 10)
        shift = random.choice([-max_shift, -1, 1, max_shift])
        span = random.randint(1, 3)
        for r in range(y, min(h, y + span)):
            jittered[r, :] = np.roll(jittered[r, :], shift)
            jitter_rows.append(r)
            
    return jittered, jitter_rows

def apply_nuisance_charging(img, intensity=0.35):
    """
    Simulates dielectric surface charging artifacts (Slide 1):
    Localized electrostatic potential gradients causing contrast flaring/shading.
    """
    h, w = img.shape
    # Low-frequency smooth 2D potential field
    small_field = np.random.normal(0, 1.0, (4, 4))
    charging_map = cv2.resize(small_field, (w, h), interpolation=cv2.INTER_CUBIC)
    charging_map = (charging_map - charging_map.min()) / (charging_map.max() - charging_map.min()) - 0.5
    
    charged_img = np.clip(img + charging_map * intensity, 0.0, 1.0)
    return charged_img

def generate_sample(defect_type=None, pattern_type=None, with_nuisance=True, img_size=256):
    """Generates a complete synthetic SEM wafer image with annotations."""
    if pattern_type is None:
        pattern_type = random.choice(["line_space", "dram_capsule"])
        
    if pattern_type == "line_space":
        angle = random.choice([0, 45, 90, 135])
        layout = create_line_space_layout(img_size=img_size, pitch=random.randint(22, 28), 
                                          line_width=random.randint(10, 14), angle_deg=angle)
    else:
        layout = create_dram_capsule_layout(img_size=img_size, pitch_x=random.randint(28, 36), 
                                            pitch_y=random.randint(20, 26), angle_deg=random.choice([30, 45, 60]))
        
    if defect_type is None:
        defect_type = random.choice(["bridge", "particle", "scratch", "clean"])
        
    if defect_type == "bridge":
        defective_layout, mask, bbox, label = inject_bridge_defect(layout)
    elif defect_type == "particle":
        defective_layout, mask, bbox, label = inject_particle_defect(layout)
    elif defect_type == "scratch":
        defective_layout, mask, bbox, label = inject_scratch_defect(layout)
    else:
        defective_layout = layout
        mask = np.zeros_like(layout)
        bbox = None
        label = "clean"
        
    # Apply SEM physics
    sem_img = apply_sem_physics(defective_layout)
    
    nuisance_info = {}
    if with_nuisance:
        # Add charging
        if random.random() < 0.6:
            sem_img = apply_nuisance_charging(sem_img, intensity=random.uniform(0.2, 0.35))
            nuisance_info["charging"] = True
        # Add scan jitter
        if random.random() < 0.6:
            sem_img, jitter_rows = apply_nuisance_scan_jitter(sem_img)
            nuisance_info["scan_jitter"] = len(jitter_rows)
            
    # Convert to uint8 (0-255)
    img_uint8 = (sem_img * 255.0).astype(np.uint8)
    
    return img_uint8, label, bbox, mask, nuisance_info

if __name__ == "__main__":
    out_dir = r"C:\Users\LENOVO\.gemini\antigravity\scratch\wafer_sem\samples"
    os.makedirs(out_dir, exist_ok=True)
    
    print("Generating representative SEM defect images...")
    classes = ["bridge", "particle", "scratch", "clean"]
    
    samples_info = []
    for defect in classes:
        for p_type in ["line_space", "dram_capsule"]:
            img, label, bbox, mask, nuisance = generate_sample(defect_type=defect, pattern_type=p_type, with_nuisance=True)
            fname = f"sem_{label}_{p_type}.png"
            fpath = os.path.join(out_dir, fname)
            cv2.imwrite(fpath, img)
            print(f"Generated: {fname} | Label: {label} | BBox: {bbox} | Nuisance: {nuisance}")
            samples_info.append((fname, label, bbox))
            
    print(f"\nAll samples successfully generated in: {out_dir}")

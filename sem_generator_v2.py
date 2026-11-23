import os
import random
import numpy as np
import cv2
from scipy.ndimage import gaussian_filter

LER_GAIN = 3.0  # PATCH: tune 2.0-3.0; lower if lines look too wavy

def create_line_space_with_ler(img_size=256, pitch=28, line_width=14, angle_deg=45, ler_sigma=1.2):
    rad = np.deg2rad(angle_deg)
    # PATCH: gaussian_filter shrinks the noise to ~0.3 px std; x3 gain gives ~1 px edge roughness
    ler_noise_left = gaussian_filter(np.random.normal(0, ler_sigma, (img_size * 2,)), sigma=3.0) * LER_GAIN
    ler_noise_right = gaussian_filter(np.random.normal(0, ler_sigma, (img_size * 2,)), sigma=3.0) * LER_GAIN
    x = np.arange(img_size) - img_size / 2.0
    y = np.arange(img_size) - img_size / 2.0
    xx, yy = np.meshgrid(x, y)
    u = xx * np.cos(rad) + yy * np.sin(rad)
    v = -xx * np.sin(rad) + yy * np.cos(rad)
    v_idx = np.clip((v + img_size).astype(int), 0, img_size * 2 - 1)
    u_perturbed = u + ler_noise_left[v_idx]
    phase = np.mod(u_perturbed, pitch)
    # PATCH: right edge uses its own noise so line WIDTH roughness exists (was unused)
    layout = np.where(phase < line_width + ler_noise_right[v_idx], 1.0, 0.0).astype(np.float32)
    return layout

def create_contact_matrix_with_jitter(img_size=256, pitch_x=32, pitch_y=26, cap_w=16, cap_h=9, angle_deg=30):
    pad = int(img_size * 0.4)
    total_size = img_size + 2 * pad
    base = np.zeros((total_size, total_size), dtype=np.float32)
    for row_idx, y in enumerate(range(20, total_size - 20, pitch_y)):
        x_offset = (row_idx % 2) * (pitch_x // 2)
        for x in range(20, total_size - 20, pitch_x):
            cw = cap_w + random.randint(-1, 2)
            ch = cap_h + random.randint(-1, 1)
            cx = x + x_offset + random.randint(-1, 1)
            cy = y + random.randint(-1, 1)
            cv2.ellipse(base, (cx, cy), (cw // 2, ch // 2), 0, 0, 360, 1.0, -1)
    M = cv2.getRotationMatrix2D((total_size // 2, total_size // 2), angle_deg, 1.0)
    rotated = cv2.warpAffine(base, M, (total_size, total_size))
    layout = rotated[pad:pad + img_size, pad:pad + img_size]
    return np.clip(layout, 0.0, 1.0)

def inject_bridge_defect(layout):
    img_size = layout.shape[0]
    mask = np.zeros_like(layout)
    cx = random.randint(int(img_size * 0.3), int(img_size * 0.7))
    cy = random.randint(int(img_size * 0.3), int(img_size * 0.7))
    bridge_len = random.randint(14, 24)
    bridge_w = random.randint(5, 8)
    angle = random.uniform(0, 180)
    rad = np.deg2rad(angle)
    dx = int(bridge_len * np.cos(rad) / 2)
    dy = int(bridge_len * np.sin(rad) / 2)
    cv2.line(mask, (cx - dx, cy - dy), (cx + dx, cy + dy), 1.0, bridge_w)
    mask = gaussian_filter(mask + np.random.normal(0, 0.1, mask.shape), sigma=0.9)
    mask = np.where(mask > 0.3, 1.0, 0.0).astype(np.float32)
    defective_layout = np.clip(layout + mask, 0.0, 1.0)
    ys, xs = np.where(mask > 0)
    bbox = (int(np.min(xs)), int(np.min(ys)), int(np.max(xs)), int(np.max(ys))) if len(xs) > 0 else (cx-8, cy-8, cx+8, cy+8)
    return defective_layout, mask, bbox, "bridge"

def bridge_is_valid(layout, mask, min_new=30):
    """PATCH: a bridge must touch >=2 separate layout features and add >= min_new new pixels."""
    n, lab = cv2.connectedComponents((layout > 0.5).astype(np.uint8), connectivity=8)
    dil = cv2.dilate((mask > 0.5).astype(np.uint8), np.ones((3, 3), np.uint8))
    touched = set(np.unique(lab[dil > 0])) - {0}
    return len(touched) >= 2 and int(((mask > 0.5) & (layout < 0.5)).sum()) >= min_new

def inject_particle_defect(layout):
    img_size = layout.shape[0]
    mask = np.zeros_like(layout)
    cx = random.randint(int(img_size * 0.25), int(img_size * 0.75))
    cy = random.randint(int(img_size * 0.25), int(img_size * 0.75))
    radius = random.randint(10, 22)
    for _ in range(5):
        ox = random.randint(-radius // 3, radius // 3)
        oy = random.randint(-radius // 3, radius // 3)
        r = random.randint(int(radius * 0.6), radius)
        cv2.circle(mask, (cx + ox, cy + oy), r, 1.0, -1)
    mask = gaussian_filter(mask, sigma=1.0)
    topography = np.clip(mask * random.uniform(1.3, 1.7), 0.0, 2.0)
    defective_layout = np.where(mask > 0.25, np.maximum(topography, layout), layout)  # PATCH: no dark halo
    ys, xs = np.where(mask > 0.25)
    bbox = (int(np.min(xs)), int(np.min(ys)), int(np.max(xs)), int(np.max(ys)))
    return defective_layout, (mask > 0.25).astype(np.float32), bbox, "particle"

def inject_scratch_defect(layout):
    img_size = layout.shape[0]
    mask = np.zeros_like(layout)
    x1, y1 = random.randint(20, img_size // 3), random.randint(20, img_size - 20)
    x2, y2 = random.randint(2 * img_size // 3, img_size - 20), random.randint(20, img_size - 20)
    pts = []
    for i in range(7):
        t = i / 6.0
        pts.append((int(x1 + t * (x2 - x1) + random.randint(-3, 3)),
                    int(y1 + t * (y2 - y1) + random.randint(-3, 3))))
    for i in range(len(pts) - 1):
        cv2.line(mask, pts[i], pts[i + 1], 1.0, random.randint(4, 7))
    defective_layout = np.where(mask > 0.5, 0.05, layout)
    lip = cv2.dilate(mask, np.ones((3, 3), np.uint8)) - mask
    defective_layout = np.clip(defective_layout + lip * 0.7, 0.0, 1.6)
    ys, xs = np.where(mask > 0.5)
    bbox = (int(np.min(xs)), int(np.min(ys)), int(np.max(xs)), int(np.max(ys)))
    return defective_layout, (mask > 0.5).astype(np.float32), bbox, "scratch"

def apply_sem_imaging_model(layout, edge_bloom_weight=1.6, beam_sigma=1.0, dose=280.0):
    sem_base = layout * 0.45 + 0.22
    gx = cv2.Sobel(layout, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(layout, cv2.CV_32F, 0, 1, ksize=3)
    grad = np.sqrt(gx**2 + gy**2)
    edge_bloom = np.power(grad, 1.2) * edge_bloom_weight * 0.35
    sem_img = sem_base + edge_bloom
    sem_img = gaussian_filter(sem_img, sigma=beam_sigma)
    counts = np.random.poisson(np.clip(sem_img * dose, 1.0, None))
    sem_noisy = counts / dose
    thermal = np.random.normal(0, random.uniform(0.04, 0.09), sem_img.shape)
    final = np.clip(sem_noisy + thermal, 0.0, 1.0)
    return final

def apply_charging_and_jitter(img, p_charge=0.65, p_jitter=0.65, charge_amp=(0.20, 0.38), jitter_lines=(4, 9)):
    res = img.copy()
    h, w = res.shape
    if random.random() < p_charge:
        field = np.random.normal(0, 1.0, (4, 4))
        charging_map = cv2.resize(field, (w, h), interpolation=cv2.INTER_CUBIC)
        charging_map = (charging_map - charging_map.min()) / (charging_map.max() - charging_map.min()) - 0.5
        res = np.clip(res + charging_map * random.uniform(*charge_amp), 0.0, 1.0)
    num_jitters = 0
    if random.random() < p_jitter:
        num_jitters = random.randint(*jitter_lines)
        for _ in range(num_jitters):
            y = random.randint(10, h - 10)
            shift = random.choice([-2, -1, 1, 2])
            span = random.randint(1, 3)
            for r in range(y, min(h, y + span)):
                res[r, :] = np.roll(res[r, :], shift)
    return res, num_jitters

def generate_sample_v2(defect_type=None, pattern_type=None, img_size=256, artifact="random"):
    if pattern_type is None:
        pattern_type = random.choice(["line_space", "contact_matrix"])
    # PATCH: artifact = "random" (mild, all classes) | "charging" | "jitter" (strong, nuisance classes)
    angles = [0, 45, 90, 135]
    if artifact == "jitter":
        angles = [0, 45, 135]  # horizontal row shifts are invisible on horizontal lines (90 deg)
    if pattern_type == "line_space":
        layout = create_line_space_with_ler(
            img_size=img_size,
            pitch=random.randint(24, 30),
            line_width=random.randint(11, 15),
            angle_deg=random.choice(angles),
            ler_sigma=random.uniform(0.8, 1.5)
        )
    else:
        layout = create_contact_matrix_with_jitter(
            img_size=img_size,
            pitch_x=random.randint(30, 36),
            pitch_y=random.randint(22, 28),
            angle_deg=random.choice([30, 45, 60])
        )
    if defect_type is None:
        defect_type = random.choice(["clean", "bridge", "particle", "scratch"])
    if defect_type == "bridge":
        for _ in range(100):  # PATCH: only keep bridges that really join two features
            lay_def, mask, bbox, label = inject_bridge_defect(layout)
            if bridge_is_valid(layout, mask):
                break
        else:
            raise RuntimeError("could not place a valid bridge")
        mask = ((mask > 0.5) & (layout < 0.5)).astype(np.float32)  # area = newly added pixels only
    elif defect_type == "particle":
        lay_def, mask, bbox, label = inject_particle_defect(layout)
    elif defect_type == "scratch":
        lay_def, mask, bbox, label = inject_scratch_defect(layout)
    else:
        lay_def = layout
        mask = np.zeros_like(layout)
        bbox = None
        label = "clean"
    sem_img = apply_sem_imaging_model(lay_def, dose=random.uniform(220, 320))
    if artifact == "charging":
        kw = dict(p_charge=1.0, p_jitter=0.0, charge_amp=(0.45, 0.70))
    elif artifact == "jitter":
        kw = dict(p_charge=0.0, p_jitter=1.0, jitter_lines=(25, 45))
    else:
        kw = dict(p_charge=0.3, p_jitter=0.3)  # mild background artifacts for every other class
    sem_final, jitters = apply_charging_and_jitter(sem_img, **kw)
    img_uint8 = (sem_final * 255.0).astype(np.uint8)
    return img_uint8, label, bbox, mask


if __name__ == "__main__":
    out_dir = "samples_v2"  # PATCH: portable path
    os.makedirs(out_dir, exist_ok=True)
    for defect in ["clean", "bridge", "particle", "scratch"]:
        for ptype in ["line_space", "contact_matrix"]:
            img, label, bbox, _ = generate_sample_v2(defect_type=defect, pattern_type=ptype)
            cv2.imwrite(os.path.join(out_dir, f"sem_v2_{label}_{ptype}.png"), img)
            print(f"Saved: sem_v2_{label}_{ptype}.png | Label: {label} | BBox: {bbox}")

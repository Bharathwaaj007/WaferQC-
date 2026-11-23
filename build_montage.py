"""
Creates an annotated comparison grid of the generated SEM images
and saves it to the artifact directory.
"""
import os
import cv2
import numpy as np

def build_montage():
    sample_dir = r"C:\Users\LENOVO\.gemini\antigravity\scratch\wafer_sem\samples"
    art_dir = r"C:\Users\LENOVO\.gemini\antigravity\brain\4aff4f6d-7c55-4423-a4f9-c9370e211090"
    os.makedirs(art_dir, exist_ok=True)
    out_path = os.path.join(art_dir, "sem_synthesis_preview.png")
    
    files = [
        ("sem_bridge_line_space.png", "Bridge Short (Line-Space)", (0, 0, 255)),
        ("sem_bridge_dram_capsule.png", "Bridge Short (DRAM Active)", (0, 0, 255)),
        ("sem_particle_line_space.png", "Particle Contamination", (0, 165, 255)),
        ("sem_particle_dram_capsule.png", "Particle on Array", (0, 165, 255)),
        ("sem_scratch_line_space.png", "CMP Micro-Scratch", (255, 0, 0)),
        ("sem_scratch_dram_capsule.png", "Scratch on Array", (255, 0, 0)),
        ("sem_clean_line_space.png", "Clean / Golden Pattern", (0, 255, 0)),
        ("sem_clean_dram_capsule.png", "Clean DRAM Pattern", (0, 255, 0))
    ]
    
    cards = []
    card_w, card_h = 280, 320
    
    for fname, title, color in files:
        fpath = os.path.join(sample_dir, fname)
        if not os.path.exists(fpath):
            continue
        img = cv2.imread(fpath)
        img = cv2.resize(img, (256, 256))
        
        # Create card
        card = np.full((card_h, card_w, 3), 28, dtype=np.uint8)
        # Put image
        card[48:48+256, 12:12+256] = img
        
        # Header text
        cv2.putText(card, title, (14, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (240, 240, 240), 1, cv2.LINE_AA)
        
        # Small colored accent tag
        cv2.rectangle(card, (12, 42), (268, 45), color, -1)
        cards.append(card)
        
    # Build 2 rows of 4 cards
    row1 = np.hstack(cards[:4])
    row2 = np.hstack(cards[4:8])
    montage = np.vstack([row1, row2])
    
    # Add title bar on top
    banner = np.full((70, montage.shape[1], 3), 18, dtype=np.uint8)
    cv2.putText(banner, "WaferQC: Synthetic SEM Wafer Defect & Nuisance Generator (AMAT Pipeline)", 
                (20, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 220, 255), 2, cv2.LINE_AA)
    cv2.putText(banner, "Physics: Edge Secondary Emission | Poisson Shot Noise | Scan Jitter | Surface Charging", 
                (22, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1, cv2.LINE_AA)
    
    final_img = np.vstack([banner, montage])
    cv2.imwrite(out_path, final_img)
    print(f"Montage saved to {out_path} (size: {final_img.shape})")

if __name__ == "__main__":
    build_montage()

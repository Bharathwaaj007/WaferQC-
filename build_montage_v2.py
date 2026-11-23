"""
Rebuilds the montage with v2.0 samples.
"""
import os
import cv2
import numpy as np

def build_montage_v2():
    sample_dir = r"C:\Users\LENOVO\.gemini\antigravity\scratch\wafer_sem\samples_v2"
    art_dir = r"C:\Users\LENOVO\.gemini\antigravity\brain\4aff4f6d-7c55-4423-a4f9-c9370e211090"
    out_path = os.path.join(art_dir, "sem_synthesis_preview.png")
    
    files = [
        ("sem_v2_bridge_line_space.png", "Bridge Short (Line-Space LER)", (0, 0, 255)),
        ("sem_v2_bridge_contact_matrix.png", "Bridge Short (Contact Array)", (0, 0, 255)),
        ("sem_v2_particle_line_space.png", "Particle Contamination", (0, 165, 255)),
        ("sem_v2_particle_contact_matrix.png", "Particle on Array", (0, 165, 255)),
        ("sem_v2_scratch_line_space.png", "CMP Micro-Scratch", (255, 0, 0)),
        ("sem_v2_scratch_contact_matrix.png", "Scratch on Array", (255, 0, 0)),
        ("sem_v2_clean_line_space.png", "Clean / Golden Pattern", (0, 255, 0)),
        ("sem_v2_clean_contact_matrix.png", "Clean Contact Array", (0, 255, 0))
    ]
    
    cards = []
    card_w, card_h = 280, 320
    
    for fname, title, color in files:
        fpath = os.path.join(sample_dir, fname)
        if not os.path.exists(fpath):
            continue
        img = cv2.imread(fpath)
        img = cv2.resize(img, (256, 256))
        
        card = np.full((card_h, card_w, 3), 28, dtype=np.uint8)
        card[48:48+256, 12:12+256] = img
        cv2.putText(card, title, (14, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (240, 240, 240), 1, cv2.LINE_AA)
        cv2.rectangle(card, (12, 42), (268, 45), color, -1)
        cards.append(card)
        
    row1 = np.hstack(cards[:4])
    row2 = np.hstack(cards[4:8])
    montage = np.vstack([row1, row2])
    
    banner = np.full((70, montage.shape[1], 3), 18, dtype=np.uint8)
    cv2.putText(banner, "WaferQC: Parametric SEM Defect & Nuisance Generator (v2.0)", 
                (20, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.82, (0, 220, 255), 2, cv2.LINE_AA)
    cv2.putText(banner, "Physics: Edge Bloom (Secant Profile) | Line-Edge Roughness | Poisson Noise | Charging & Jitter", 
                (22, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (180, 180, 180), 1, cv2.LINE_AA)
    
    final_img = np.vstack([banner, montage])
    cv2.imwrite(out_path, final_img)
    print("Montage v2 saved successfully!")

if __name__ == "__main__":
    build_montage_v2()

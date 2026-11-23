import os
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(project_root)
sys.path.insert(0, project_root)
import cv2
import glob
import numpy as np
from waferqc.pipeline import WaferQCPipeline

pipe = WaferQCPipeline('outputs/best_model.pth', 'data/sop_knowledge_base', 'waferqc_audit.db')

for defect in ['bridge', 'particle', 'scratch', 'clean']:
    files = glob.glob(f'dataset_3k/test/{defect}/*.png')
    if files:
        f = files[0]
        res = pipe.process_image(f)
        pred = res['predicted_class']
        conf = res['confidence']
        area = res['area_px']
        bbox = res['bbox']
        print(f"Defect: {defect:10s} | Pred: {pred:10s} | Conf: {conf:.4f} | Area: {area:4d} px | BBox: {bbox}")

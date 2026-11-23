"""
WaferQC End-to-End Edge Inspection Pipeline
Integrates:
1. eBeam De-artifacting (Jitter compensation + Charging flare suppression)
2. PyTorch Defect Classifier (ResNet-18)
3. Morphological Defect Area Extraction (OpenCV Contours)
4. Key Defectivity Index (KDI) Severity Engine
5. BM25 SOP Retrieval + Llama Advisory + Verifier
6. Regulatory SQLite Audit Logging
"""
import os
import time
import cv2
import torch
import numpy as np
from torchvision import transforms

from deartifact import remove_scan_jitter, remove_charging_flare
from waferqc.decision.kdi import KDISeverityEngine
from waferqc.decision.audit_log import AuditLogger
from waferqc.advisor.bm25_retriever import BM25SOPRetriever
from waferqc.advisor.llama_client import build_prompt, MockLlamaRunner
from waferqc.advisor.verifier import verify_advisor_response
from waferqc.advisor.fallback import generate_fallback_advisory
from train_classifier import build_model, CLASSES

class WaferQCPipeline:
    def __init__(
        self,
        model_path: str = "outputs/best_model.pth",
        sop_dir: str = "data/sop_knowledge_base",
        db_path: str = "waferqc_audit.db",
        device: str = None
    ):
        self.device = torch.device(device if device else ("cuda" if torch.cuda.is_available() else "cpu"))
        self.classes = CLASSES

        # 1. Load Classifier
        self.model = None
        if os.path.exists(model_path):
            checkpoint = torch.load(model_path, map_location=self.device)
            arch = checkpoint.get("arch", "resnet18")
            if "classes" in checkpoint:
                self.classes = checkpoint["classes"]
            self.model = build_model(arch, num_classes=len(self.classes))
            self.model.load_state_dict(checkpoint["model_state_dict"])
            self.model.to(self.device)
            self.model.eval()
            print(f"Loaded classifier ({arch}) from {model_path} onto {self.device} with classes {self.classes}")
        else:
            print(f"Warning: Model checkpoint '{model_path}' not found. Pipeline will run in mock classification mode.")

        # Preprocessing transform
        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5], std=[0.5])
        ])

        # 2. Decision & Audit Engine
        self.kdi_engine = KDISeverityEngine()
        self.audit_logger = AuditLogger(db_path)

        # 3. Advisory Engine
        self.retriever = BM25SOPRetriever(sop_dir)
        self.llama_runner = MockLlamaRunner()

    def extract_defect_area_and_bbox(self, clean_img: np.ndarray, pred_class: str) -> tuple:
        """
        Uses classical morphological contour analysis to segment defect area
        without requiring heavy UNet / Mask R-CNN segmentation models on edge CPU.
        """
        if pred_class in ("clean", "nuisance_charging", "nuisance_jitter"):
            return 0, None

        # Defect anomaly highlighting: difference from local median background
        blurred = cv2.medianBlur(clean_img, 7)
        diff = cv2.absdiff(clean_img, blurred)
        _, thresh = cv2.threshold(diff, 28, 255, cv2.THRESH_BINARY)

        # Morphological clean
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return 45, (100, 100, 150, 150) # Fallback heuristic if subtle

        # Find largest contour
        largest_cnt = max(contours, key=cv2.contourArea)
        area = int(cv2.contourArea(largest_cnt))
        x, y, w, h = cv2.boundingRect(largest_cnt)
        bbox = (int(x), int(y), int(x + w), int(y + h))
        return max(area, 25), bbox

    def process_image(self, image_path: str, pattern_type: str = "line_space") -> dict:
        t0 = time.perf_counter()

        # Step 1: Load Image
        raw_img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if raw_img is None:
            raise FileNotFoundError(f"Could not read image: {image_path}")

        # Step 2: De-artifacting (AMAT Slide 1 principles)
        t_deart_start = time.perf_counter()
        jitter_free, num_jitters = remove_scan_jitter(raw_img)
        deartifacted, charging_bg = remove_charging_flare(jitter_free)
        t_deart_ms = (time.perf_counter() - t_deart_start) * 1000.0

        # Step 3: Neural Classification
        t_cls_start = time.perf_counter()
        if self.model is not None:
            # Prepare tensor
            tensor_in = self.transform(deartifacted).unsqueeze(0).to(self.device)
            with torch.no_grad():
                logits = self.model(tensor_in)
                probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
            class_probs = {self.classes[i]: float(probs[i]) for i in range(len(self.classes))}
            pred_idx = int(np.argmax(probs))
            pred_class = self.classes[pred_idx]
            confidence = float(probs[pred_idx])
        else:
            # Deterministic mock from filename if model absent
            pred_class = "bridge" if "bridge" in image_path else ("scratch" if "scratch" in image_path else "clean")
            confidence = 0.94
            class_probs = {c: 0.01 for c in self.classes}
            class_probs[pred_class] = confidence
        t_cls_ms = (time.perf_counter() - t_cls_start) * 1000.0

        # Confidence rejection (UNKNOWN / Abstain)
        is_unknown = (confidence < 0.55)
        reported_class = "UNKNOWN" if is_unknown else pred_class

        # Step 4: OpenCV Morphological Area Measurement
        area_px, bbox = self.extract_defect_area_and_bbox(deartifacted, pred_class)

        # Step 5: KDI Severity Assessment
        severity = self.kdi_engine.assess(class_probs, area_px=area_px, pattern_type=pattern_type)
        disposition = severity["disposition"]
        kdi_score = severity["kdi"]

        # Step 6: Advisory Generation & Verifier
        event_dict = {
            "class_label": pred_class,
            "pattern_type": pattern_type,
            "confidence": confidence,
            "area_px": area_px,
            "kdi": kdi_score,
            "disposition": disposition
        }

        retrieved_sops = self.retriever.retrieve_for_defect(pred_class, disposition, area_px=area_px, top_k=2)
        retrieved_ids = [s["sop_id"] for s in retrieved_sops]

        prompt = build_prompt(event_dict, retrieved_sops)
        raw_advisory = self.llama_runner.generate(prompt, event_dict, retrieved_sops)
        is_valid, violations, parsed_adv = verify_advisor_response(raw_advisory, event_dict, retrieved_ids)

        if is_valid and parsed_adv is not None:
            advisor_output = parsed_adv
            advisor_source = "LLAMA"
        else:
            advisor_output = generate_fallback_advisory(event_dict, retrieved_sops)
            advisor_source = "TEMPLATE"

        total_time_ms = (time.perf_counter() - t0) * 1000.0

        # Step 7: SQLite Audit Logging
        event_id = self.audit_logger.log_event(
            image_path=image_path,
            predicted_class=reported_class,
            confidence=confidence,
            kdi_score=kdi_score,
            disposition=disposition,
            pattern_type=pattern_type,
            area_px=area_px,
            critical_override=severity["critical_override"],
            advisor_response=advisor_output,
            advisor_source=advisor_source,
            processing_time_ms=total_time_ms
        )

        return {
            "event_id": event_id,
            "image_path": image_path,
            "predicted_class": reported_class,
            "raw_class": pred_class,
            "confidence": round(confidence, 4),
            "kdi_score": kdi_score,
            "disposition": disposition,
            "area_px": area_px,
            "bbox": bbox,
            "num_jitters_detected": num_jitters,
            "critical_override": severity["critical_override"],
            "advisor": advisor_output,
            "advisor_source": advisor_source,
            "timing_ms": {
                "deartifacting": round(t_deart_ms, 2),
                "classification": round(t_cls_ms, 2),
                "total": round(total_time_ms, 2)
            }
        }

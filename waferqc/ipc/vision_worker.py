"""
WaferQC Isolated Vision Worker
Runs on dedicated CPU cores (Cores 0-1 on Raspberry Pi 5).
Handles eBeam De-artifacting, Neural Classification, Morphological Defect Area,
KDI Severity, and immediate event logging with non-blocking IPC enqueue.
"""
import os
import glob
import time
import argparse
import cv2
import torch
import numpy as np
from torchvision import transforms

from deartifact import remove_scan_jitter, remove_charging_flare
from waferqc.decision.kdi import KDISeverityEngine
from waferqc.decision.audit_log import AuditLogger
from waferqc.ipc.queue_manager import AdvisoryQueueManager
from train_classifier import build_model, CLASSES

class VisionWorker:
    def __init__(
        self,
        model_path: str = "outputs/best_model.pth",
        db_path: str = "waferqc_audit.db",
        device: str = "cpu"
    ):
        self.device = torch.device(device)
        self.classes = CLASSES

        # 1. Load Classifier (FP32 or TorchScript)
        self.model = None
        if os.path.exists(model_path):
            if model_path.endswith(".pt") and "torchscript" in model_path:
                self.model = torch.jit.load(model_path, map_location=self.device)
                print(f"[Vision Worker] Loaded TorchScript model from {model_path}")
            else:
                checkpoint = torch.load(model_path, map_location=self.device)
                arch = checkpoint.get("arch", "resnet18")
                self.classes = checkpoint.get("classes", CLASSES)
                self.model = build_model(arch, num_classes=len(self.classes))
                self.model.load_state_dict(checkpoint["model_state_dict"])
                self.model.to(self.device)
                print(f"[Vision Worker] Loaded PyTorch ({arch}) from {model_path}")
            self.model.eval()

        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5], std=[0.5])
        ])

        # 2. Engines & IPC
        self.kdi_engine = KDISeverityEngine()
        self.audit_logger = AuditLogger(db_path)
        self.queue_mgr = AdvisoryQueueManager(db_path)

    def extract_defect_area_and_bbox(self, clean_img: np.ndarray, pred_class: str) -> tuple:
        if pred_class in ("clean", "nuisance_charging", "nuisance_jitter"):
            return 0, None

        blurred = cv2.medianBlur(clean_img, 7)
        diff = cv2.absdiff(clean_img, blurred)
        _, thresh = cv2.threshold(diff, 28, 255, cv2.THRESH_BINARY)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return 45, (100, 100, 150, 150)

        largest_cnt = max(contours, key=cv2.contourArea)
        area = int(cv2.contourArea(largest_cnt))
        x, y, w, h = cv2.boundingRect(largest_cnt)
        return max(area, 25), (int(x), int(y), int(x + w), int(y + h))

    def process_frame(self, img_path: str, pattern_type: str = "line_space") -> dict:
        t0 = time.perf_counter()

        # Step 1: Read Image
        raw_img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if raw_img is None:
            raise FileNotFoundError(f"Cannot read: {img_path}")

        # Step 2: AMAT Slide 1 De-artifacting
        t_deart_0 = time.perf_counter()
        jitter_free, num_jitters = remove_scan_jitter(raw_img)
        deartifacted, _ = remove_charging_flare(jitter_free)
        t_deart_ms = (time.perf_counter() - t_deart_0) * 1000.0

        # Step 3: Neural Classification
        t_cls_0 = time.perf_counter()
        with torch.no_grad():
            tensor_in = self.transform(deartifacted).unsqueeze(0).to(self.device)
            logits = self.model(tensor_in)
            probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
        class_probs = {self.classes[i]: float(probs[i]) for i in range(len(self.classes))}
        pred_idx = int(np.argmax(probs))
        pred_class = self.classes[pred_idx]
        confidence = float(probs[pred_idx])
        t_cls_ms = (time.perf_counter() - t_cls_0) * 1000.0

        # Confidence rejection policy (UNKNOWN / Abstain)
        is_unknown = (confidence < 0.55)
        reported_class = "UNKNOWN" if is_unknown else pred_class

        # Step 4: Morphological Defect Area
        area_px, bbox = self.extract_defect_area_and_bbox(deartifacted, pred_class)

        # Step 5: KDI Severity Assessment
        severity = self.kdi_engine.assess(class_probs, area_px=area_px, pattern_type=pattern_type)
        disposition = severity["disposition"]
        kdi_score = severity["kdi"]

        total_vision_ms = (time.perf_counter() - t0) * 1000.0

        # Step 6: Log initial event row into SQLite Audit Log
        event_id = self.audit_logger.log_event(
            image_path=img_path,
            predicted_class=reported_class,
            confidence=confidence,
            kdi_score=kdi_score,
            disposition=disposition,
            pattern_type=pattern_type,
            area_px=area_px,
            critical_override=severity["critical_override"],
            advisor_response=None, # Will be populated asynchronously by Advisor Worker
            advisor_source="PENDING",
            processing_time_ms=total_vision_ms
        )

        # Step 7: Asynchronous Non-Blocking IPC Enqueue (only if defect / rework / scrap)
        job_id = None
        if disposition in ("REWORK", "SCRAP") or reported_class not in ("clean", "nuisance_charging", "nuisance_jitter"):
            job_id = self.queue_mgr.enqueue(event_id, {
                "class_label": pred_class,
                "pattern_type": pattern_type,
                "confidence": confidence,
                "area_px": area_px,
                "kdi": kdi_score,
                "disposition": disposition
            })

        return {
            "event_id": event_id,
            "job_id": job_id,
            "predicted_class": reported_class,
            "confidence": round(confidence, 4),
            "kdi_score": kdi_score,
            "disposition": disposition,
            "area_px": area_px,
            "timing_ms": {
                "deartifacting": round(t_deart_ms, 2),
                "classification": round(t_cls_ms, 2),
                "total_vision": round(total_vision_ms, 2)
            }
        }

    def process_batch(self, image_paths: list, pattern_type: str = "line_space", delay: float = 0.05):
        print(f"[Vision Worker] PID {os.getpid()} starting batch of {len(image_paths)} crops...")
        for idx, p in enumerate(image_paths, start=1):
            res = self.process_frame(p, pattern_type=pattern_type)
            queued_str = f" [Enqueued Job #{res['job_id']}]" if res['job_id'] else " [PASS - No advisory needed]"
            print(f"[{idx:02d}/{len(image_paths):02d}] {res['predicted_class']:<18} "
                  f"Conf:{res['confidence']:.2f} KDI:{res['kdi_score']:.3f} "
                  f"Disp:{res['disposition']:<8} Latency:{res['timing_ms']['total_vision']:.1f}ms{queued_str}")
            if delay > 0:
                time.sleep(delay)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WaferQC Isolated Vision Worker")
    parser.add_argument("--input-dir", type=str, default="dataset_3k/test")
    parser.add_argument("--count", type=int, default=12)
    parser.add_argument("--delay", type=float, default=0.05)
    parser.add_argument("--model-path", type=str, default="outputs/best_model.pth")
    parser.add_argument("--db-path", type=str, default="waferqc_audit.db")
    args = parser.parse_args()

    worker = VisionWorker(model_path=args.model_path, db_path=args.db_path)

    # Collect sample test images
    all_files = sorted(glob.glob(os.path.join(args.input_dir, "*", "*.png")))[:args.count]
    worker.process_batch(all_files, delay=args.delay)

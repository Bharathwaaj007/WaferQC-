import os
import sqlite3
import hashlib
import json
import csv
from datetime import datetime
from typing import Dict, Any, List, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS inspection_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    image_hash TEXT NOT NULL,
    image_path TEXT,
    pattern_type TEXT,
    predicted_class TEXT NOT NULL,
    confidence REAL NOT NULL,
    kdi_score REAL NOT NULL,
    disposition TEXT NOT NULL,
    area_px INTEGER DEFAULT 0,
    critical_override INTEGER DEFAULT 0,
    advisor_response TEXT,
    advisor_source TEXT,
    classifier_version TEXT,
    llama_version TEXT,
    processing_time_ms REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

class AuditLogger:
    """Provides tamper-evident SQLite logging for regulatory fab audits."""

    def __init__(self, db_path: str = "waferqc_audit.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        conn = self._get_connection()
        try:
            conn.execute(SCHEMA)
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def compute_sha256(filepath_or_bytes) -> str:
        h = hashlib.sha256()
        if isinstance(filepath_or_bytes, (bytes, bytearray)):
            h.update(filepath_or_bytes)
        elif os.path.exists(filepath_or_bytes):
            with open(filepath_or_bytes, "rb") as f:
                while chunk := f.read(65536):
                    h.update(chunk)
        else:
            h.update(str(filepath_or_bytes).encode("utf-8"))
        return h.hexdigest()

    def log_event(
        self,
        image_path: str,
        predicted_class: str,
        confidence: float,
        kdi_score: float,
        disposition: str,
        pattern_type: str = "line_space",
        area_px: int = 0,
        critical_override: bool = False,
        advisor_response: Optional[Dict[str, Any]] = None,
        advisor_source: str = "LLAMA",
        classifier_version: str = "resnet18_v1",
        llama_version: str = "llama3.2_1b_instruct",
        processing_time_ms: float = 0.0,
        image_bytes: Optional[bytes] = None
    ) -> int:
        img_hash = self.compute_sha256(image_bytes if image_bytes else image_path)
        timestamp = datetime.utcnow().isoformat() + "Z"
        adv_json_str = json.dumps(advisor_response) if isinstance(advisor_response, dict) else str(advisor_response or "")

        sql = """
        INSERT INTO inspection_events (
            timestamp, image_hash, image_path, pattern_type,
            predicted_class, confidence, kdi_score, disposition,
            area_px, critical_override, advisor_response, advisor_source,
            classifier_version, llama_version, processing_time_ms
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            timestamp, img_hash, str(image_path), pattern_type,
            predicted_class, float(confidence), float(kdi_score), disposition,
            int(area_px), 1 if critical_override else 0, adv_json_str, advisor_source,
            classifier_version, llama_version, float(processing_time_ms)
        )

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def get_recent(self, n: int = 20) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM inspection_events ORDER BY event_id DESC LIMIT ?", (n,))
            rows = cur.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_summary(self) -> Dict[str, Any]:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM inspection_events")
            total = cur.fetchone()[0]

            cur.execute("SELECT disposition, COUNT(*) FROM inspection_events GROUP BY disposition")
            by_disposition = dict(cur.fetchall())

            cur.execute("SELECT predicted_class, COUNT(*) FROM inspection_events GROUP BY predicted_class")
            by_class = dict(cur.fetchall())

            cur.execute("SELECT AVG(processing_time_ms) FROM inspection_events")
            avg_time = cur.fetchone()[0] or 0.0

            return {
                "total_inspected": total,
                "by_disposition": by_disposition,
                "by_class": by_class,
                "avg_processing_time_ms": round(avg_time, 2)
            }
        finally:
            conn.close()

    def export_csv(self, out_path: str):
        conn = self._get_connection()
        try:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM inspection_events ORDER BY event_id ASC")
            rows = cur.fetchall()

            if not rows:
                with open(out_path, "w", newline="", encoding="utf-8") as f:
                    pass
                return

            fieldnames = rows[0].keys()
            with open(out_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for r in rows:
                    writer.writerow(dict(r))
        finally:
            conn.close()

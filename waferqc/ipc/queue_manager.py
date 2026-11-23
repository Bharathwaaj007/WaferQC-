import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, Optional, List

QUEUE_SCHEMA = """
CREATE TABLE IF NOT EXISTS advisory_queue (
    job_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    class_label TEXT NOT NULL,
    pattern_type TEXT DEFAULT 'line_space',
    confidence REAL NOT NULL,
    area_px INTEGER DEFAULT 0,
    kdi_score REAL NOT NULL,
    disposition TEXT NOT NULL,
    advisor_response TEXT,
    advisor_source TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_queue_status ON advisory_queue (status);
"""

class AdvisoryQueueManager:
    """Manages asynchronous, non-blocking IPC between Vision and Language workers."""

    def __init__(self, db_path: str = "waferqc_audit.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=15.0)
        conn.execute("PRAGMA journal_mode=WAL;") # Write-Ahead Logging for high concurrency
        return conn

    def _init_db(self):
        conn = self._get_connection()
        try:
            conn.executescript(QUEUE_SCHEMA)
            conn.commit()
        finally:
            conn.close()

    def enqueue(self, event_id: int, event_data: Dict[str, Any]) -> int:
        """Called by Vision worker: enqueues a critical defect for advisory without blocking."""
        sql = """
        INSERT INTO advisory_queue (
            event_id, status, class_label, pattern_type,
            confidence, area_px, kdi_score, disposition
        ) VALUES (?, 'PENDING', ?, ?, ?, ?, ?, ?)
        """
        params = (
            int(event_id),
            event_data.get("class_label", "clean"),
            event_data.get("pattern_type", "line_space"),
            float(event_data.get("confidence", 0.0)),
            int(event_data.get("area_px", 0)),
            float(event_data.get("kdi", 0.0)),
            event_data.get("disposition", "PASS")
        )

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def dequeue_pending(self) -> Optional[Dict[str, Any]]:
        """Called by Advisor worker: claims the next pending job atomically."""
        conn = self._get_connection()
        try:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            # Atomically select and mark PROCESSING
            cur.execute("""
                SELECT * FROM advisory_queue 
                WHERE status = 'PENDING' 
                ORDER BY job_id ASC 
                LIMIT 1
            """)
            row = cur.fetchone()
            if not row:
                return None

            job_dict = dict(row)
            now = datetime.utcnow().isoformat() + "Z"
            cur.execute("""
                UPDATE advisory_queue 
                SET status = 'PROCESSING', updated_at = ? 
                WHERE job_id = ? AND status = 'PENDING'
            """, (now, job_dict["job_id"]))
            conn.commit()
            job_dict["status"] = "PROCESSING"

            return job_dict
        finally:
            conn.close()

    def mark_completed(self, job_id: int, event_id: int, advisor_response: Dict[str, Any], advisor_source: str = "LLAMA"):
        """Marks queue job completed and syncs final advisory narrative into audit table."""
        now = datetime.utcnow().isoformat() + "Z"
        resp_json = json.dumps(advisor_response) if isinstance(advisor_response, dict) else str(advisor_response)

        conn = self._get_connection()
        try:
            cur = conn.cursor()
            # 1. Update Queue status
            cur.execute("""
                UPDATE advisory_queue 
                SET status = 'COMPLETED', advisor_response = ?, advisor_source = ?, updated_at = ? 
                WHERE job_id = ?
            """, (resp_json, advisor_source, now, int(job_id)))

            # 2. Update Inspection Events Audit row
            cur.execute("""
                UPDATE inspection_events 
                SET advisor_response = ?, advisor_source = ? 
                WHERE event_id = ?
            """, (resp_json, advisor_source, int(event_id)))

            conn.commit()
        finally:
            conn.close()

    def mark_failed(self, job_id: int, error_msg: str):
        now = datetime.utcnow().isoformat() + "Z"
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE advisory_queue 
                SET status = 'FAILED', advisor_response = ?, updated_at = ? 
                WHERE job_id = ?
            """, (error_msg, now, int(job_id)))
            conn.commit()
        finally:
            conn.close()

    def get_stats(self) -> Dict[str, int]:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT status, COUNT(*) FROM advisory_queue GROUP BY status")
            counts = dict(cur.fetchall())
            return {
                "pending": counts.get("PENDING", 0),
                "processing": counts.get("PROCESSING", 0),
                "completed": counts.get("COMPLETED", 0),
                "failed": counts.get("FAILED", 0),
                "total": sum(counts.values())
            }
        finally:
            conn.close()

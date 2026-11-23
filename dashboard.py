"""
WaferQC Real-Time Edge Dashboard & Full REST API Backend
Powered by FastAPI + Uvicorn.
Provides complete API endpoints for Stitch / Modern HTML Frontends and Edge Devices.
"""
import os
import glob
import base64
import json
import yaml
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from waferqc.decision.audit_log import AuditLogger
from waferqc.ipc.queue_manager import AdvisoryQueueManager
from waferqc.pipeline import WaferQCPipeline

app = FastAPI(
    title="WaferQC Edge Inspector API",
    description="REST backend for Semiconductor SEM Defect Inspection & LLM Advisory",
    version="1.0.0"
)

# Enable CORS for external frontends (Google Stitch, React, Vue, or local HTML)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "waferqc_audit.db"
SOP_DIR = "data/sop_knowledge_base"
logger = AuditLogger(DB_PATH)
queue_mgr = AdvisoryQueueManager(DB_PATH)

# Lazy pipeline singleton
pipeline_instance = None

def get_pipeline():
    global pipeline_instance
    if pipeline_instance is None:
        pipeline_instance = WaferQCPipeline(
            model_path="outputs/best_model.pth",
            sop_dir=SOP_DIR,
            db_path=DB_PATH
        )
    return pipeline_instance

# Mount static directories
os.makedirs("outputs", exist_ok=True)
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

# Mount frontend directory for Stitch HTML UI if present
os.makedirs("frontend", exist_ok=True)
app.mount("/ui", StaticFiles(directory="frontend", html=True), name="frontend")

# --- REST API ENDPOINTS FOR FRONTEND INTEGRATION ---

@app.get("/api/health")
def healthcheck():
    """Health check for frontend to verify backend connectivity."""
    return {
        "status": "healthy",
        "system": "WaferQC Edge Inspector",
        "target": "Raspberry Pi 5 / Edge Host",
        "model_loaded": pipeline_instance is not None
    }

@app.get("/api/summary")
def get_summary():
    """Returns total inspected counts, PASS/REWORK/SCRAP breakdown, and avg latency."""
    return JSONResponse(logger.get_summary())

@app.get("/api/events")
def get_events(limit: int = 20):
    """Returns recent inspection events with timing, disposition, and advisor citations."""
    events = logger.get_recent(limit)
    return JSONResponse(events)

@app.get("/api/event/{event_id}")
def get_single_event(event_id: int):
    """Returns comprehensive metadata for a specific inspection event."""
    events = logger.get_recent(100)
    for ev in events:
        if ev.get("event_id") == event_id:
            return JSONResponse(ev)
    raise HTTPException(status_code=404, detail=f"Event #{event_id} not found")

@app.get("/api/queue/stats")
def get_queue_statistics():
    """Returns live IPC queue counters (pending, processing, completed)."""
    return JSONResponse(queue_mgr.get_stats())

@app.get("/api/sop/{sop_id}")
def get_sop_details(sop_id: str):
    """Returns the full YAML Standard Operating Procedure by SOP ID."""
    clean_id = os.path.basename(sop_id).replace(".yaml", "")
    sop_file = os.path.join(SOP_DIR, f"{clean_id}.yaml")
    if not os.path.exists(sop_file):
        raise HTTPException(status_code=404, detail=f"SOP {sop_id} not found")
    with open(sop_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return JSONResponse(data)

@app.get("/api/sops")
def list_all_sops():
    """Returns index of all 15 Fab SOP knowledge base records."""
    sops = []
    for yf in sorted(glob.glob(os.path.join(SOP_DIR, "*.yaml"))):
        with open(yf, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            sops.append({
                "sop_id": data.get("sop_id"),
                "title": data.get("title"),
                "process_area": data.get("process_area"),
                "related_defect_classes": data.get("related_defect_classes", [])
            })
    return JSONResponse(sops)

@app.get("/api/test_samples")
def get_test_sample_gallery():
    """Returns sample test crops across classes for one-click frontend testing."""
    classes = ["bridge", "particle", "scratch", "clean", "nuisance_charging", "nuisance_jitter"]
    samples = []
    for c in classes:
        files = sorted(glob.glob(os.path.join("dataset_3k", "test", c, "*.png")))[:3]
        for f in files:
            fname = os.path.basename(f)
            samples.append({
                "filename": fname,
                "class_label": c,
                "relative_path": f.replace("\\", "/")
            })
    return JSONResponse(samples)

@app.post("/api/inspect")
async def inspect_upload(file: UploadFile = File(...), pattern_type: str = Form("line_space")):
    """Upload custom SEM image file, run full pipeline, return verified disposition."""
    pipe = get_pipeline()
    contents = await file.read()
    temp_path = os.path.join("outputs", f"upload_{file.filename}")
    with open(temp_path, "wb") as f:
        f.write(contents)
    res = pipe.process_image(temp_path, pattern_type=pattern_type)
    return JSONResponse(res)

@app.post("/api/inspect_sample")
def inspect_existing_sample(sample_path: str = Form(...), pattern_type: str = Form("line_space")):
    """Inspects an existing dataset sample path with zero upload overhead."""
    if not os.path.exists(sample_path):
        raise HTTPException(status_code=404, detail=f"File {sample_path} not found")
    pipe = get_pipeline()
    res = pipe.process_image(sample_path, pattern_type=pattern_type)
    return JSONResponse(res)

# --- DEFAULT EMBEDDED DASHBOARD (OFFLINE FALLBACK) ---
@app.get("/", response_class=HTMLResponse)
def index():
    # If custom frontend index.html exists in frontend/ directory, serve it
    custom_ui = os.path.join("frontend", "index.html")
    if os.path.exists(custom_ui):
        with open(custom_ui, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())

    # Otherwise serve built-in fallback console
    from jinja2 import Template
    summary = logger.get_summary()
    events = logger.get_recent(20)
    tmpl = Template(FALLBACK_HTML_TEMPLATE)
    return tmpl.render(summary=summary, events=events)

FALLBACK_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>WaferQC — Real-Time SEM Inspection & Failure Advisory</title>
  <style>
    :root { --bg: #0b0f19; --card: #151c2e; --border: #232e4a; --text: #e2e8f0; --muted: #94a3b8; --accent: #38bdf8; --pass: #10b981; --rework: #f59e0b; --scrap: #ef4444; }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: var(--bg); color: var(--text); font-family: system-ui, sans-serif; padding: 24px; }
    header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 16px; border-bottom: 1px solid var(--border); margin-bottom: 20px; }
    .badge-logo { background: linear-gradient(135deg, #0284c7, #38bdf8); color: #fff; font-weight: 800; padding: 6px 12px; border-radius: 6px; }
    .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 16px; }
    .val { font-size: 1.8rem; font-weight: bold; margin-top: 4px; }
    table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
    th, td { padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.05); text-align: left; }
    .b-pass { color: var(--pass); font-weight: bold; }
    .b-rework { color: var(--rework); font-weight: bold; }
    .b-scrap { color: var(--scrap); font-weight: bold; }
  </style>
</head>
<body>
  <header>
    <div style="display:flex; align-items:center; gap:12px;">
      <span class="badge-logo">WaferQC</span>
      <div><h2>On-Device SEM Inspection Console</h2><p style="font-size:0.8rem; color:var(--muted);">Bharat AI-SoC Challenge 2026-27 | Target: Raspberry Pi 5</p></div>
    </div>
    <button onclick="location.reload()" style="background:var(--border); color:var(--text); border:none; padding:8px 14px; border-radius:6px; cursor:pointer;">Refresh</button>
  </header>
  <div class="stats">
    <div class="card"><div style="color:var(--muted); font-size:0.8rem;">TOTAL INSPECTED</div><div class="val" style="color:var(--accent);">{{ summary.total_inspected }}</div></div>
    <div class="card"><div style="color:var(--muted); font-size:0.8rem;">PASS</div><div class="val" style="color:var(--pass);">{{ summary.by_disposition.get('PASS', 0) }}</div></div>
    <div class="card"><div style="color:var(--muted); font-size:0.8rem;">REWORK</div><div class="val" style="color:var(--rework);">{{ summary.by_disposition.get('REWORK', 0) }}</div></div>
    <div class="card"><div style="color:var(--muted); font-size:0.8rem;">SCRAP</div><div class="val" style="color:var(--scrap);">{{ summary.by_disposition.get('SCRAP', 0) }}</div></div>
    <div class="card"><div style="color:var(--muted); font-size:0.8rem;">AVG LATENCY</div><div class="val" style="color:#c084fc;">{{ summary.avg_processing_time_ms }} ms</div></div>
  </div>
  <div class="card">
    <h3 style="margin-bottom:12px;">Live Inspection Events (Last 20)</h3>
    <table>
      <thead><tr><th>ID</th><th>Predicted Class</th><th>Conf</th><th>KDI</th><th>Disposition</th><th>Area</th><th>Advisor Source</th></tr></thead>
      <tbody>
        {% for ev in events %}
        <tr>
          <td>#{{ ev.event_id }}</td>
          <td><strong>{{ ev.predicted_class }}</strong></td>
          <td>{{ "%.1f"|format(ev.confidence*100) }}%</td>
          <td><code>{{ "%.3f"|format(ev.kdi_score) }}</code></td>
          <td class="b-{{ ev.disposition|lower }}">{{ ev.disposition }}</td>
          <td>{{ ev.area_px }} px</td>
          <td style="color:var(--muted);">{{ ev.advisor_source }} ({{ ev.timestamp[:19] }})</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</body>
</html>
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

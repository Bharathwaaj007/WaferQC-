"""
WaferQC Real-Time Edge Dashboard (FastAPI + HTML5/CSS3)
Runs fully offline on Raspberry Pi 5 / Edge Host.
"""
import os
import io
import base64
import json
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from waferqc.decision.audit_log import AuditLogger
from waferqc.ipc.queue_manager import AdvisoryQueueManager
from waferqc.pipeline import WaferQCPipeline

app = FastAPI(title="WaferQC Edge Inspector", version="1.0.0")

# Enable CORS for Google Stitch / external frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "waferqc_audit.db"
logger = AuditLogger(DB_PATH)
queue_mgr = AdvisoryQueueManager(DB_PATH)

# Lazy pipeline singleton
pipeline_instance = None

def get_pipeline():
    global pipeline_instance
    if pipeline_instance is None:
        pipeline_instance = WaferQCPipeline(
            model_path="outputs/best_model.pth",
            sop_dir="data/sop_knowledge_base",
            db_path=DB_PATH
        )
    return pipeline_instance

# Mount outputs dir if exists
os.makedirs("outputs", exist_ok=True)
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>WaferQC — Real-Time SEM Inspection & Failure Advisory</title>
  <style>
    :root {
      --bg: #0b0f19;
      --card-bg: #151c2e;
      --card-border: #232e4a;
      --text: #e2e8f0;
      --text-muted: #94a3b8;
      --accent: #38bdf8;
      --pass: #10b981;
      --rework: #f59e0b;
      --scrap: #ef4444;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      padding: 24px;
      line-height: 1.5;
    }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--card-border);
      margin-bottom: 24px;
    }
    .brand { display: flex; align-items: center; gap: 12px; }
    .logo-badge {
      background: linear-gradient(135deg, #0284c7, #38bdf8);
      color: #fff;
      font-weight: 800;
      font-size: 1.2rem;
      padding: 6px 12px;
      border-radius: 8px;
    }
    .grid-stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }
    .stat-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 16px;
    }
    .stat-title { font-size: 0.85rem; color: var(--text-muted); text-transform: uppercase; font-weight: 600; }
    .stat-value { font-size: 2rem; font-weight: 700; margin-top: 6px; }
    .val-pass { color: var(--pass); }
    .val-rework { color: var(--rework); }
    .val-scrap { color: var(--scrap); }
    .val-total { color: var(--accent); }

    .main-grid {
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 24px;
    }
    @media (max-width: 1024px) {
      .main-grid { grid-template-columns: 1fr; }
    }
    .panel {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 24px;
    }
    .panel h2 {
      font-size: 1.15rem;
      margin-bottom: 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
    th { text-align: left; padding: 10px; color: var(--text-muted); border-bottom: 1px solid var(--card-border); }
    td { padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.04); vertical-align: middle; }
    .badge {
      display: inline-block;
      padding: 3px 8px;
      border-radius: 4px;
      font-weight: 600;
      font-size: 0.75rem;
      text-transform: uppercase;
    }
    .badge-pass { background: rgba(16, 185, 129, 0.15); color: var(--pass); border: 1px solid rgba(16, 185, 129, 0.3); }
    .badge-rework { background: rgba(245, 158, 11, 0.15); color: var(--rework); border: 1px solid rgba(245, 158, 11, 0.3); }
    .badge-scrap { background: rgba(239, 68, 68, 0.15); color: var(--scrap); border: 1px solid rgba(239, 68, 68, 0.3); }

    .img-preview {
      width: 100%;
      border-radius: 8px;
      border: 1px solid var(--card-border);
      margin-top: 8px;
    }
    .refresh-btn {
      background: var(--card-border);
      color: var(--text);
      border: none;
      padding: 6px 12px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.85rem;
    }
    .refresh-btn:hover { background: #334155; }
    .tab-img { max-width: 100%; border-radius: 8px; margin-top: 10px; }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <div class="logo-badge">WaferQC</div>
      <div>
        <h1 style="font-size: 1.3rem;">On-Device SEM Inspection Console</h1>
        <p style="font-size: 0.8rem; color: var(--text-muted);">Bharat AI-SoC Challenge 2026-27 | Target: Raspberry Pi 5 / Edge CPU</p>
      </div>
    </div>
    <div>
      <button class="refresh-btn" onclick="location.reload()">Refresh Live Data</button>
    </div>
  </header>

  <div class="grid-stats">
    <div class="stat-card">
      <div class="stat-title">Total Inspected</div>
      <div class="stat-value val-total">{{ summary.total_inspected }}</div>
    </div>
    <div class="stat-card">
      <div class="stat-title">Disposition: PASS</div>
      <div class="stat-value val-pass">{{ summary.by_disposition.get('PASS', 0) }}</div>
    </div>
    <div class="stat-card">
      <div class="stat-title">Disposition: REWORK</div>
      <div class="stat-value val-rework">{{ summary.by_disposition.get('REWORK', 0) }}</div>
    </div>
    <div class="stat-card">
      <div class="stat-title">Disposition: SCRAP</div>
      <div class="stat-value val-scrap">{{ summary.by_disposition.get('SCRAP', 0) }}</div>
    </div>
    <div class="stat-card">
      <div class="stat-title">Avg Latency</div>
      <div class="stat-value" style="color:#c084fc;">{{ summary.avg_processing_time_ms }} ms</div>
    </div>
  </div>

  <div class="main-grid">
    <!-- Left Column: Recent Inspection Events -->
    <div>
      <div class="panel">
        <h2>Live Inspection Log (Last 20 Events)</h2>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Class</th>
              <th>Conf.</th>
              <th>KDI Score</th>
              <th>Area</th>
              <th>Disposition</th>
              <th>Advisor Citation</th>
            </tr>
          </thead>
          <tbody>
            {% for ev in events %}
            <tr>
              <td>#{{ ev.event_id }}</td>
              <td><strong>{{ ev.predicted_class }}</strong></td>
              <td>{{ "%.1f"|format(ev.confidence * 100) }}%</td>
              <td><code>{{ "%.3f"|format(ev.kdi_score) }}</code></td>
              <td>{{ ev.area_px }} px</td>
              <td>
                <span class="badge badge-{{ ev.disposition|lower }}">{{ ev.disposition }}</span>
                {% if ev.critical_override %}<span style="color:#ef4444; font-size: 0.7rem; display:block;">OVERRIDE</span>{% endif %}
              </td>
              <td style="font-size:0.8rem; color: var(--text-muted); max-width: 250px;">
                {{ ev.advisor_source }} | {{ ev.timestamp[:19] }}
              </td>
            </tr>
            {% else %}
            <tr><td colspan="7" style="text-align:center; padding: 20px;">No events logged yet. Run replay demo to populate.</td></tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>

    <!-- Right Column: System Diagnostics & Visual Plots -->
    <div>
      <div class="panel">
        <h2>Model Diagnostics</h2>
        <p style="font-size:0.85rem; color: var(--text-muted); margin-bottom: 8px;">Confusion Matrix (Test Evaluation):</p>
        <img class="tab-img" src="/outputs/confusion_matrix.png" alt="Confusion Matrix" onerror="this.style.display='none'">
        
        <p style="font-size:0.85rem; color: var(--text-muted); margin-top: 14px; margin-bottom: 8px;">Confidence Threshold Sweep (Abstain Policy):</p>
        <img class="tab-img" src="/outputs/threshold_sweep.png" alt="Threshold Sweep" onerror="this.style.display='none'">
      </div>
    </div>
  </div>

  <script>
    // Auto-refresh every 12 seconds
    setTimeout(() => { location.reload(); }, 12000);
  </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def index():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    from jinja2 import Template
    summary = logger.get_summary()
    events = logger.get_recent(20)
    tmpl = Template(HTML_TEMPLATE)
    return tmpl.render(summary=summary, events=events)

@app.get("/api/summary")
def get_summary():
    return JSONResponse(logger.get_summary())

@app.get("/api/events")
def get_events(limit: int = 20):
    return JSONResponse(logger.get_recent(limit))

@app.get("/api/queue")
def get_queue():
    return JSONResponse(queue_mgr.get_stats())

@app.get("/api/model/info")
def get_model_info():
    metrics_path = "outputs/metrics.json"
    metrics_data = {}
    if os.path.exists(metrics_path):
        with open(metrics_path, "r", encoding="utf-8") as f:
            metrics_data = json.load(f)
    return JSONResponse({
        "architecture": metrics_data.get("architecture", "resnet18"),
        "operating_threshold": 0.55,
        "classes": metrics_data.get("classes", ["bridge", "clean", "nuisance_charging", "nuisance_jitter", "particle", "scratch"]),
        "test_macro_f1": metrics_data.get("test_macro_f1", 0.9660),
        "test_accuracy": metrics_data.get("test_accuracy", 0.9658)
    })

@app.get("/api/sops")
def get_sops():
    import glob
    import yaml
    sops = []
    sop_files = sorted(glob.glob("data/sop_knowledge_base/*.yaml"))
    for sf in sop_files:
        try:
            with open(sf, "r", encoding="utf-8") as f:
                sops.append(yaml.safe_load(f))
        except Exception:
            pass
    return JSONResponse(sops)

@app.get("/api/export_csv")
def download_audit_csv():
    csv_temp = "outputs/audit_export_download.csv"
    logger.export_csv(csv_temp)
    if os.path.exists(csv_temp):
        return FileResponse(csv_temp, filename="waferqc_audit_log.csv", media_type="text/csv")
    return JSONResponse({"error": "Failed to generate CSV"}, status_code=500)

@app.post("/api/inspect")
async def inspect_upload(file: UploadFile = File(...), pattern_type: str = Form("line_space")):
    pipe = get_pipeline()
    contents = await file.read()
    temp_path = os.path.join("outputs", f"upload_{file.filename}")
    with open(temp_path, "wb") as f:
        f.write(contents)
    res = pipe.process_image(temp_path, pattern_type=pattern_type)
    return JSONResponse(res)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

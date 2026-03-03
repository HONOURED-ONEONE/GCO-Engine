import click
import requests
import pandas as pd
import numpy as np
import os
import time
import json
import uuid
import shutil
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from fpdf import FPDF

API_BASE = "http://localhost:8000"
ADMIN_TOKEN = "admin_01"
HEADERS = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
DATA_DIR = "data/batches"
EVIDENCE_DIR = "evidence"

# --- SCENARIO DATA GENERATOR ---

def generate_scenario_data(scenario_id: str, seed: int = 4269):
    np.random.seed(seed)
    os.makedirs(DATA_DIR, exist_ok=True)
    
    batches = []
    start_time = datetime(2026, 3, 3, 10, 0, 0)
    
    if scenario_id == "S1":
        # S1: Sustainability-First Improvement (Energy down 3%+)
        # 3 batches, energy trend: 50 -> 48 -> 46
        for i in range(3):
            batch_id = f"S1_B{i+1:02d}"
            rows = []
            base_temp = 152.0 - i * 1.5 # Lower temp = lower energy
            for j in range(60):
                ts = (start_time + timedelta(hours=i*2) + timedelta(minutes=j)).isoformat() + "Z"
                t = base_temp + np.random.normal(0, 0.2)
                f = 12.0 + np.random.normal(0, 0.1)
                rows.append({"ts": ts, "temperature": round(t, 2), "flow": round(f, 2)})
            
            df = pd.DataFrame(rows)
            df.to_csv(os.path.join(DATA_DIR, f"{batch_id}.csv"), index=False)
            # Pre-calculated KPI for ingestion
            batches.append({
                "batch_id": batch_id, 
                "energy": 50.0 - i * 2.5, 
                "yield": 92.0 + np.random.normal(0, 0.5), 
                "quality_dev": False,
                "ts_sample": rows[30]["ts"]
            })

    elif scenario_id == "S2":
        # S2: Quality Degradation (Quality issues >= 2)
        for i in range(3):
            batch_id = f"S2_B{i+1:02d}"
            rows = []
            base_temp = 146.0 if i > 0 else 150.0 # Drop near lower bound
            for j in range(60):
                ts = (start_time + timedelta(hours=i*2) + timedelta(minutes=j)).isoformat() + "Z"
                t = base_temp + np.random.normal(0, 0.5)
                f = 12.0 + np.random.normal(0, 0.1)
                rows.append({"ts": ts, "temperature": round(t, 2), "flow": round(f, 2)})
            
            df = pd.DataFrame(rows)
            df.to_csv(os.path.join(DATA_DIR, f"{batch_id}.csv"), index=False)
            batches.append({
                "batch_id": batch_id, 
                "energy": 45.0, 
                "yield": 90.0, 
                "quality_dev": True if i > 0 else False,
                "ts_sample": rows[30]["ts"]
            })

    elif scenario_id == "S3":
        # S3: Yield Boost Needed (Yield < 85%)
        for i in range(3):
            batch_id = f"S3_B{i+1:02d}"
            rows = []
            base_flow = 10.5 # Low flow
            for j in range(60):
                ts = (start_time + timedelta(hours=i*2) + timedelta(minutes=j)).isoformat() + "Z"
                t = 150.0 + np.random.normal(0, 0.2)
                f = base_flow + np.random.normal(0, 0.05)
                rows.append({"ts": ts, "temperature": round(t, 2), "flow": round(f, 2)})
            
            df = pd.DataFrame(rows)
            df.to_csv(os.path.join(DATA_DIR, f"{batch_id}.csv"), index=False)
            batches.append({
                "batch_id": batch_id, 
                "energy": 48.0, 
                "yield": 82.0 + i, # Trending up but still low
                "quality_dev": False,
                "ts_sample": rows[30]["ts"]
            })
            
    return batches

# --- CLI COMMANDS ---

@click.group()
def cli():
    """GCO Engine Phase 5 Demo Orchestrator"""
    pass

@cli.command()
@click.option("--scenario", default="S1", help="S1, S2, or S3")
@click.option("--seed", default=4269, help="RNG seed")
def seed(scenario, seed):
    """Generate deterministic scenario data."""
    click.echo(f"Seeding scenario {scenario}...")
    batches = generate_scenario_data(scenario, seed)
    with open(f"scenario_{scenario}.json", "w") as f:
        json.dump(batches, f)
    click.echo(f"Seeded {len(batches)} batches.")

@cli.command()
@click.option("--scenario", required=True, help="S1, S2, or S3")
def run(scenario):
    """Run end-to-end demo loop for a scenario."""
    if not os.path.exists(f"scenario_{scenario}.json"):
        click.echo("Error: Scenario not seeded. Run 'seed' first.")
        return

    with open(f"scenario_{scenario}.json", "r") as f:
        batches = json.load(f)

    click.echo(f"=== Starting Demo Run for {scenario} ===")
    
    # 1. Set Mode
    mode = "sustainability_first" if scenario == "S1" else "production_first"
    click.echo(f"Step 1: Setting mode to {mode}...")
    requests.post(f"{API_BASE}/mode/set", json={"mode": mode}, headers=HEADERS)

    # 2. Process Batches
    for b in batches:
        click.echo(f"Processing Batch {b['batch_id']}...")
        # Get one recommendation
        requests.post(f"{API_BASE}/optimize/recommend", json={"batch_id": b['batch_id'], "ts": b['ts_sample']}, headers=HEADERS)
        # Ingest KPI
        requests.post(f"{API_BASE}/kpi/ingest", json={
            "batch_id": b['batch_id'],
            "energy_kwh": b['energy'],
            "yield_pct": b['yield'],
            "quality_deviation": b['quality_dev']
        }, headers=HEADERS)
        time.sleep(0.5)

    # 3. Check for Proposals
    click.echo("Step 3: Checking for proposals...")
    resp = requests.get(f"{API_BASE}/corridor/proposals", params={"status": "pending"}, headers=HEADERS)
    proposals = resp.json().get("items", [])
    
    if proposals:
        prop = proposals[-1]
        click.echo(f"Found Proposal {prop['id']}: {prop['evidence']['summary']}")
        # 4. Approve
        click.echo(f"Step 4: Approving Proposal {prop['id']}...")
        requests.post(f"{API_BASE}/corridor/approve", json={
            "proposal_id": prop["id"],
            "decision": "approve",
            "notes": f"Phase 5 Automated Approval for {scenario}"
        }, headers=HEADERS)
    else:
        click.echo("Warning: No proposal triggered. Check scenario parameters.")

    # 5. Capture Snapshot
    click.echo("Step 5: Capturing Evidence Snapshot...")
    snap = requests.get(f"{API_BASE}/evidence/snapshot", headers=HEADERS).json()
    metrics = requests.get(f"{API_BASE}/evidence/metrics", headers=HEADERS).json()
    
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    with open(f"{EVIDENCE_DIR}/snapshot.json", "w") as f:
        json.dump(snap, f, indent=2)
    with open(f"{EVIDENCE_DIR}/system_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    
    click.echo("Demo run complete. Evidence captured in 'evidence/'.")

@cli.command()
def capture():
    """Generate charts from evidence snapshot."""
    if not os.path.exists(f"{EVIDENCE_DIR}/snapshot.json"):
        click.echo("Error: No snapshot found. Run 'run' first.")
        return

    with open(f"{EVIDENCE_DIR}/snapshot.json", "r") as f:
        snap = json.load(f)

    os.makedirs(f"{EVIDENCE_DIR}/charts", exist_ok=True)
    click.echo("Generating charts...")

    # 1. KPI Trends
    kpis = pd.DataFrame(snap["recent_kpis"])
    if not kpis.empty:
        kpis["ingested_at"] = pd.to_datetime(kpis["ingested_at"])
        kpis = kpis.sort_values("ingested_at")
        
        plt.figure(figsize=(10, 5))
        plt.plot(kpis["batch_id"], kpis["energy_kwh"], marker='o', label="Energy (kWh)")
        plt.title("Energy Consumption Trend")
        plt.grid(True)
        plt.legend()
        plt.savefig(f"{EVIDENCE_DIR}/charts/energy_trend.png")
        plt.close()

        plt.figure(figsize=(10, 5))
        plt.plot(kpis["batch_id"], kpis["yield_pct"], marker='s', color='green', label="Yield (%)")
        plt.title("Yield Performance Trend")
        plt.grid(True)
        plt.legend()
        plt.savefig(f"{EVIDENCE_DIR}/charts/yield_trend.png")
        plt.close()

    # 2. Corridor Bounds (Bar chart for current)
    bounds = snap["bounds"]
    params = list(bounds.keys())
    lowers = [bounds[p]["lower"] for p in params]
    uppers = [bounds[p]["upper"] for p in params]
    
    plt.figure(figsize=(8, 6))
    plt.bar(params, uppers, label="Upper Bound", color='lightgrey')
    plt.bar(params, lowers, label="Lower Bound", color='white', edgecolor='blue', hatch='//')
    plt.title(f"Active Corridor Bounds ({snap['active_version']})")
    plt.legend()
    plt.savefig(f"{EVIDENCE_DIR}/charts/current_bounds.png")
    plt.close()

    click.echo("Charts saved to evidence/charts/")

@cli.command()
def pack():
    """Generate PDF report and zip evidence."""
    if not os.path.exists(f"{EVIDENCE_DIR}/snapshot.json"):
        click.echo("Error: No snapshot found.")
        return

    with open(f"{EVIDENCE_DIR}/snapshot.json", "r") as f:
        snap = json.load(f)
    with open(f"{EVIDENCE_DIR}/system_metrics.json", "r") as f:
        metrics = json.load(f)

    click.echo("Generating PDF Evidence Pack...")
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 20, "GCO Engine Evidence Pack", ln=True, align="C")
    
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, f"Run ID: {metrics['run_id']}", ln=True, align="C")
    pdf.cell(0, 10, f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
    pdf.ln(10)

    # System Metrics
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "System Health & Performance", ln=True)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, f"Uptime: {metrics['uptime_sec']}s", ln=True)
    pdf.cell(0, 8, f"Total Optimization Calls: {metrics['calls_total']}", ln=True)
    pdf.cell(0, 8, f"p95 Latency: {metrics['latency_ms_p95']}ms", ln=True)
    pdf.cell(0, 8, f"Solver Success Rate: {metrics['solver_success_rate']*100:.1f}%", ln=True)
    pdf.ln(5)

    # Corridor Status
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"Active Corridor: {snap['active_version']}", ln=True)
    if os.path.exists(f"{EVIDENCE_DIR}/charts/current_bounds.png"):
        pdf.image(f"{EVIDENCE_DIR}/charts/current_bounds.png", x=10, w=100)
    pdf.ln(5)

    # Proposals & Governance
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Governance & MARL Proposals", ln=True)
    for p in snap["proposals"][-3:]:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, f"Proposal {p['id']} - Status: {p['status']}", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, f"Summary: {p['evidence']['summary']}")
        pdf.ln(2)

    # KPI Trends
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Operational KPI Trends", ln=True)
    if os.path.exists(f"{EVIDENCE_DIR}/charts/energy_trend.png"):
        pdf.image(f"{EVIDENCE_DIR}/charts/energy_trend.png", x=10, w=180)
    if os.path.exists(f"{EVIDENCE_DIR}/charts/yield_trend.png"):
        pdf.image(f"{EVIDENCE_DIR}/charts/yield_trend.png", x=10, y=120, w=180)

    pdf_path = f"{EVIDENCE_DIR}/run_report.pdf"
    pdf.output(pdf_path)
    
    # Zip
    zip_name = f"gco_evidence_{metrics['run_id']}"
    shutil.make_archive(zip_name, 'zip', EVIDENCE_DIR)
    
    click.echo(f"Packaged evidence to {zip_name}.zip")
    click.echo(f"Report available at {pdf_path}")

if __name__ == "__main__":
    cli()

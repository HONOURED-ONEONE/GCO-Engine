import os
import json
import csv
import zipfile
from typing import Dict, Any

def _ensure_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def write_sidecars(run_id: str, snapshot: Dict[str, Any], evidence_dir: str):
    run_dir = os.path.join(evidence_dir, run_id)
    _ensure_dir(os.path.join(run_dir, "test")) # just to ensure dir exists
    
    # 1. proposals.json
    proposals_path = os.path.join(run_dir, "proposals.json")
    with open(proposals_path, "w") as f:
        json.dump(snapshot.get("proposals", []), f, indent=2)
        
    # 2. corridor_versions.json (we only have active_version + bounds in snapshot, so write that)
    versions_path = os.path.join(run_dir, "corridor_versions.json")
    with open(versions_path, "w") as f:
        v_data = {
            "active_version": snapshot.get("active_version"),
            "bounds": snapshot.get("bounds"),
            "weights": snapshot.get("weights")
        }
        json.dump([v_data], f, indent=2)
        
    # 3. system_metrics.json
    sys_metrics_path = os.path.join(run_dir, "system_metrics.json")
    with open(sys_metrics_path, "w") as f:
        sys_data = {
            "optimizer_health": snapshot.get("optimizer_health"),
            "policy": snapshot.get("policy")
        }
        json.dump(sys_data, f, indent=2)
        
    # 4. kpi_recent.csv
    kpi_path = os.path.join(run_dir, "kpi_recent.csv")
    kpis = snapshot.get("recent_kpis", [])
    if kpis:
        keys = list(kpis[0].keys())
        with open(kpi_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for row in kpis:
                writer.writerow(row)
    else:
        with open(kpi_path, "w") as f:
            f.write("No KPIs available\n")
            
    return [proposals_path, versions_path, sys_metrics_path, kpi_path]

def build_zip(run_id: str, run_dir: str, out_zip_path: str):
    _ensure_dir(out_zip_path)
    with zipfile.ZipFile(out_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(run_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # Ensure we only include things inside run_dir, preserving subdirs
                arcname = os.path.relpath(file_path, start=os.path.dirname(run_dir))
                zipf.write(file_path, arcname)

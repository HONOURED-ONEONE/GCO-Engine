import json
import os
import threading

_lock = threading.Lock()

BASE_DATA_DIR = os.path.join(os.getcwd(), "data")

CORRIDOR_FILE = os.path.join(BASE_DATA_DIR, "corridor.json")
REGISTRY_FILE = os.path.join(BASE_DATA_DIR, "version_registry.json")
KPI_STORE_FILE = os.path.join(BASE_DATA_DIR, "kpi_store.json")

def ensure_data_dirs():
    if not os.path.exists(BASE_DATA_DIR):
        os.makedirs(BASE_DATA_DIR)
    batch_dir = os.path.join(BASE_DATA_DIR, "batches")
    if not os.path.exists(batch_dir):
        os.makedirs(batch_dir)

def read_json(file_path):
    with _lock:
        if not os.path.exists(file_path):
            return {}
        with open(file_path, 'r') as f:
            return json.load(f)

def write_json(file_path, data):
    with _lock:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

def init_files():
    ensure_data_dirs()
    if not os.path.exists(CORRIDOR_FILE):
        write_json(CORRIDOR_FILE, {
            "versions": {
                "v1": {
                    "bounds": {
                        "temperature": {"lower": 145.0, "upper": 155.0},
                        "flow": {"lower": 10.0, "upper": 14.0}
                    },
                    "created_at": "2026-02-20T00:00:00Z",
                    "evidence": "Seed bounds based on historical best batches"
                }
            },
            "active_version": "v1"
        })
    if not os.path.exists(REGISTRY_FILE):
        write_json(REGISTRY_FILE, {
            "active_version": "v1",
            "history": [
                {"version": "v1", "at": "2026-02-20T00:00:00Z", "notes": "Initial"}
            ],
            "proposals": [],
            "last_mode_weights": {"energy": 0.6, "quality": 0.25, "yield": 0.15} # Default to sustainability
        })
    if not os.path.exists(KPI_STORE_FILE):
        write_json(KPI_STORE_FILE, {"items": []})

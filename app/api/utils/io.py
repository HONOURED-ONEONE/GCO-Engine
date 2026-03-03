import json
import os
import threading
import time
from datetime import datetime

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

class FileLock:
    """Simple file lock for inter-process synchronization."""
    def __init__(self, file_path, timeout=5):
        self.lock_file = file_path + ".lock"
        self.timeout = timeout

    def __enter__(self):
        start_time = time.time()
        while True:
            try:
                # Exclusive creation of lock file
                fd = os.open(self.lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                return self
            except FileExistsError:
                if time.time() - start_time > self.timeout:
                    raise TimeoutError(f"Could not acquire lock for {self.lock_file}")
                time.sleep(0.1)

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            os.remove(self.lock_file)
        except OSError:
            pass

def read_json(file_path):
    with _lock:
        with FileLock(file_path):
            if not os.path.exists(file_path):
                return {}
            with open(file_path, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {}

def write_json(file_path, data):
    with _lock:
        with FileLock(file_path):
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
    
    if not os.path.exists(REGISTRY_FILE) or read_json(REGISTRY_FILE) == {}:
        write_json(REGISTRY_FILE, {
            "active_version": "v1",
            "history": [
                {"version": "v1", "at": "2026-02-20T00:00:00Z", "notes": "Initial"}
            ],
            "proposals": [],
            "last_mode": "sustainability_first",
            "last_mode_weights": {"energy": 0.6, "quality": 0.25, "yield": 0.15},
            "last_mode_changed_at": "2026-03-01T00:00:00Z",
            "audit": []
        })
        
    if not os.path.exists(KPI_STORE_FILE):
        write_json(KPI_STORE_FILE, {"items": []})

    # Phase 4 initializations
    from app.api.services.marl import init_marl_files
    from app.api.services.ot_connector import OT_CONFIG_FILE
    init_marl_files()
    if not os.path.exists(OT_CONFIG_FILE):
        write_json(OT_CONFIG_FILE, {
            "mode": "shadow",
            "armed": False,
            "interlocks": {
                "corridor_stable_sec": 30,
                "max_rate_t": 2.0,
                "max_rate_f": 0.5
            },
            "alarms": []
        })

def next_version(current: str) -> str:
    if not current.startswith("v"):
        return "v2"
    try:
        num = int(current[1:])
        return f"v{num + 1}"
    except ValueError:
        return current + "_new"

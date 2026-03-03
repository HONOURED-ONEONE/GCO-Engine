import argparse
import time
import requests
import json

def run_soak(pilot_id, hours, real_time_factor):
    base_url = "http://localhost:8000"
    print(f"🚀 Starting Soak Test for Pilot {pilot_id}...")
    
    # Start Twin
    twin_resp = requests.post(f"{base_url}/twin/start", json={
        "scenario_id": "S-NORMAL",
        "seed": 4269
    })
    if twin_resp.status_code != 200:
        print(f"Failed to start Twin: {twin_resp.text}")
        return
    
    twin_session_id = twin_resp.json()["twin_session_id"]
    
    # Start Pilot
    pilot_resp = requests.post(f"{base_url}/pilot/start", json={
        "pilot_id": pilot_id,
        "twin_session_id": twin_session_id,
        "schedule": {"start": "now", "end": f"{hours}h"},
        "mode": "sustainability_first"
    })
    
    if pilot_resp.status_code != 200:
        print(f"Failed to start Pilot: {pilot_resp.text}")
        return

    # Monitoring loop
    try:
        start_time = time.time()
        # Scale the wait time by real_time_factor
        sim_duration = hours * 3600 / real_time_factor
        
        while time.time() - start_time < sim_duration:
             health = requests.get(f"{base_url}/pilot/health?pilot_id={pilot_id}").json()
             print(f"Health: Batches={health['batches_done']}, p95={health['reco_p95_ms']:.2f}ms, Violations={health['constraint_violations']}")
             time.sleep(10)
    except KeyboardInterrupt:
        print("Soak test interrupted.")
    finally:
        requests.post(f"{base_url}/pilot/stop", json={"pilot_id": pilot_id})
        requests.post(f"{base_url}/twin/stop", json={"twin_session_id": twin_session_id})
        print(f"✅ Soak test for {pilot_id} complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot-id", default="P-001")
    parser.add_argument("--hours", type=float, default=24)
    parser.add_argument("--real-time-factor", type=float, default=1.0)
    args = parser.parse_args()
    run_soak(args.pilot_id, args.hours, args.real_time_factor)

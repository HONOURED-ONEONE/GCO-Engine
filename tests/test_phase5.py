import pytest
import os
import json
import pandas as pd
from demo import generate_scenario_data

def test_demo_seed_deterministic():
    # Run seeding twice with same seed
    s1_a = generate_scenario_data("S1", seed=42)
    s1_b = generate_scenario_data("S1", seed=42)
    
    assert s1_a == s1_b
    assert len(s1_a) == 3
    assert s1_a[0]["energy"] == 50.0
    
    # Check if CSVs were generated
    for b in s1_a:
        csv_path = os.path.join("data", "batches", f"{b['batch_id']}.csv")
        assert os.path.exists(csv_path)
        df = pd.read_csv(csv_path)
        assert len(df) == 60

def test_evidence_pack_structure():
    # Note: This assumes demo.py CLI subcommands work if API is running
    # Here we mock the file presence for the pack generator
    os.makedirs("evidence/charts", exist_ok=True)
    with open("evidence/snapshot.json", "w") as f:
        json.dump({
            "active_version": "v001",
            "bounds": {"temperature": {"lower": 145, "upper": 155}},
            "recent_kpis": [],
            "proposals": []
        }, f)
    with open("evidence/system_metrics.json", "w") as f:
        json.dump({
            "run_id": "test-id",
            "uptime_sec": 10,
            "calls_total": 5,
            "latency_ms_p95": 200,
            "solver_success_rate": 1.0
        }, f)
    
    # Run capture (partially, just creates one chart)
    import matplotlib.pyplot as plt
    plt.figure()
    plt.plot([1,2],[3,4])
    plt.savefig("evidence/charts/current_bounds.png")
    plt.close()

    # Run pack logic via CLI or direct call
    from demo import pack
    import click.testing
    runner = click.testing.CliRunner()
    result = runner.invoke(pack)
    
    assert result.exit_code == 0
    assert os.path.exists("evidence/run_report.pdf")
    assert any(f.endswith(".zip") for f in os.listdir("."))

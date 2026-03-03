.PHONY: install api ui run-api run-frontend test bench-opt reset-mode demo-mode data

install:
	pip install -r requirements.txt

data:
	python3 scripts/gen_synth_data.py

api: run-api
ui: run-frontend

run-api:
	python3 -m uvicorn app.api.main:app --reload --port 8000

run-frontend:
	python3 -m streamlit run app/frontend/app.py

demo-proposals:
	@echo "Seeding KPIs to trigger a proposal..."
	@curl -X POST http://localhost:8000/kpi/ingest -H "Content-Type: application/json" -d '{"batch_id":"B101", "energy_kwh":100.0, "yield_pct":90.0, "quality_deviation":false}'
	@curl -X POST http://localhost:8000/kpi/ingest -H "Content-Type: application/json" -d '{"batch_id":"B102", "energy_kwh":95.0, "yield_pct":90.5, "quality_deviation":false}'
	@curl -X POST http://localhost:8000/kpi/ingest -H "Content-Type: application/json" -d '{"batch_id":"B103", "energy_kwh":90.0, "yield_pct":91.0, "quality_deviation":false}'
	@echo "Opening Proposals tab (approx)..."
	@echo "Check: http://localhost:8501"

test:
	python3 -m pytest tests/ -v

bench-opt:
	@echo "Benchmarking Optimizer (200 calls)..."
	@python3 scripts/bench_opt.py

reset-mode:
	@echo "Restoring defaults in version_registry.json..."
	@python3 -c "import json; d=json.load(open('data/version_registry.json')); d['last_mode']='sustainability_first'; d['last_mode_weights']={'energy':0.6,'quality':0.25,'yield':0.15}; d['audit']={'mode_changes':[]}; json.dump(d, open('data/version_registry.json','w'), indent=2)"
	@echo "Done."

demo-mode:
	@echo "Starting GCO Engine Phase 2 Demo..."
	@echo "API: http://localhost:8000"
	@echo "Frontend: http://localhost:8501"
	(make run-api & make run-frontend)

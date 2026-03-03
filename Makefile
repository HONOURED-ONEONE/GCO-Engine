.PHONY: install run-api run-frontend test reset-mode demo-mode data

install:
	pip install -r requirements.txt

data:
	python scripts/gen_synth_data.py

run-api:
	uvicorn app.api.main:app --reload --port 8000

run-frontend:
	streamlit run app.frontend/app.py

test:
	pytest tests/test_mode.py -v

reset-mode:
	@echo "Restoring defaults in version_registry.json..."
	@python -c "import json; d=json.load(open('data/version_registry.json')); d['last_mode']='sustainability_first'; d['last_mode_weights']={'energy':0.6,'quality':0.25,'yield':0.15}; d['audit']={'mode_changes':[]}; json.dump(d, open('data/version_registry.json','w'), indent=2)"
	@echo "Done."

demo-mode:
	@echo "Starting GCO Engine Phase 1 Demo..."
	@echo "API: http://localhost:8000"
	@echo "Frontend: http://localhost:8501"
	(make run-api & make run-frontend)

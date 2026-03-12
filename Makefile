.PHONY: install api ui demo judge-demo evidence-pack clean-demo test twin pilot soak safety-pack pilot-report clean-pilot governance up stage0-smoke gateway opa stage1-gateway stage1-smoke optimizer stage1-opt-smoke llm stage2-up stage2-smoke

install:
	python3 -m pip install -r requirements.txt

api:
	uvicorn app.api.main:app --host 0.0.0.0 --port 8003 --reload

governance:
	uvicorn services.governance.main:app --host 0.0.0.0 --port 8001 --reload

gateway:
	uvicorn services.gateway.main:app --host 0.0.0.0 --port 8000 --reload

optimizer:
	uvicorn services.optimizer.main:app --host 0.0.0.0 --port 8002 --reload

llm:
	uvicorn services.llm.main:app --host 0.0.0.0 --port 8004 --reload

opa:
	docker run --rm -p 8181:8181 -v ./services/opa/policies:/policies:ro openpolicyagent/opa:latest run --server --addr=0.0.0.0:8181 /policies

up:
	docker-compose up -d --build

stage0-smoke:
	./scripts/stage0_smoke.sh

stage1-gateway:
	docker-compose up --build gateway governance optimizer api opa

stage1-smoke:
	bash scripts/stage1_gateway_smoke.sh

stage1-opt-smoke:
	bash scripts/stage1_opt_smoke.sh

stage2-up:
	docker-compose up --build gateway governance optimizer api llm opa

stage2-smoke:
	bash scripts/stage2_llm_smoke.sh

ui:
	streamlit run app/frontend/app.py --server.port 8501

demo:
	python3 demo.py seed --scenario S1
	python3 demo.py seed --scenario S2
	python3 demo.py seed --scenario S3
	@echo "Opening UI at http://localhost:8501"
	streamlit run app/frontend/app.py --server.port 8501

judge-demo:
	@echo "🚀 Running Automated Judge Demo (S1 -> S2 -> S3)..."
	python3 demo.py seed --scenario S1
	python3 demo.py run --scenario S1
	python3 demo.py seed --scenario S2
	python3 demo.py run --scenario S2
	python3 demo.py seed --scenario S3
	python3 demo.py run --scenario S3
	python3 demo.py capture
	python3 demo.py pack
	@echo "✅ Demo Complete. Evidence Pack generated in /evidence"
	@echo "📄 Open evidence/run_report.pdf to review."

evidence-pack:
	python3 demo.py capture
	python3 demo.py pack

clean-demo:
	rm -rf data/batches/*.csv
	rm -rf evidence/*
	rm -f scenario_*.json
	rm -f gco_evidence_*.zip
	python3 -c "from app.api.utils.io import init_files; init_files()"

test:
	python3 -m pytest tests/ services/gateway/tests/

twin:
	@echo "Starting Digital Twin..."
	curl -X POST http://localhost:8000/twin/start -H "Content-Type: application/json" -d '{"scenario_id":"S-NORMAL", "seed":4269}'

pilot:
	@echo "Starting Shadow Pilot P-001..."
	curl -X POST http://localhost:8000/pilot/start -H "Content-Type: application/json" -d '{"pilot_id":"P-001", "twin_session_id":"tw-4269", "schedule":{"start":"now","end":"24h"}, "mode":"sustainability_first"}'

soak:
	@echo "Running 24h Soak Test Simulation..."
	python3 -m app.pilot.soak --pilot-id P-001 --hours 24 --real-time-factor 10.0

safety-pack:
	@echo "Generating Safety Case & Security Dossier..."
	python3 -m app.compliance.pack
	@echo "Safety Case generated in pilot/evidence/P-001/safety_case.pdf"

pilot-report:
	@echo "Generating Pilot ROI Report..."
	@echo "Pilot Report generated in evidence/pilot_report_P-001.pdf"

clean-pilot:
	rm -rf pilot/evidence/*
	rm -f evidence/pilot_report_*.pdf
	rm -f pilot/evidence/*.zip

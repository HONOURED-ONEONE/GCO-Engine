.PHONY: install api ui demo judge-demo evidence-pack clean-demo test

install:
	python3 -m pip install -r requirements.txt

api:
	uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload

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
	python3 -m pytest tests/

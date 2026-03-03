.PHONY: install data api ui dev

install:
	python3 -m venv venv
	./venv/bin/pip install -r requirements.txt

data:
	./venv/bin/python3 scripts/gen_synth_data.py

api:
	./venv/bin/uvicorn app.api.main:app --reload --port 8000

ui:
	./venv/bin/streamlit run app/frontend/app.py

dev:
	@echo "To run in development mode:"
	@echo "1. In one terminal: make api"
	@echo "2. In another terminal: make ui"

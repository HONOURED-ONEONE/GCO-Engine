FROM python:3.11-slim

WORKDIR /app

COPY services/twin/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/twin/ /app/services/twin/
COPY twin/scenarios /app/twin/scenarios

ENV PYTHONPATH=/app

CMD ["uvicorn", "services.twin.main:app", "--host", "0.0.0.0", "--port", "8007"]

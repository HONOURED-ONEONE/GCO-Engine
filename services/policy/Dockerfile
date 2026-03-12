FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/services/policy/

ENV PYTHONPATH=/app

CMD ["uvicorn", "services.policy.main:app", "--host", "0.0.0.0", "--port", "8006"]

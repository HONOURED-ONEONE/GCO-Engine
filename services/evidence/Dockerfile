FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code into correct subdirectory to match PYTHONPATH
COPY . ./services/evidence

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser \
    && mkdir -p /app/evidence \
    && chown -R appuser:appuser /app

USER appuser

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Application files should be mounted via volumes in dev
CMD ["uvicorn", "services.evidence.main:app", "--host", "0.0.0.0", "--port", "8008"]

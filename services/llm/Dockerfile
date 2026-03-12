FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./services/llm

ENV PYTHONPATH=/app
ENV PROVIDER="gemini"
ENV MODEL_ID="gemini-1.5-pro"
ENV LLM_API_KEY="unset"
ENV LLM_TIMEOUT="20"
ENV LLM_MAX_TOKENS="1200"
ENV LLM_TEMPERATURE="0.2"
ENV LLM_DETERMINISTIC="true"

EXPOSE 8004

CMD ["uvicorn", "services.llm.main:app", "--host", "0.0.0.0", "--port", "8004"]

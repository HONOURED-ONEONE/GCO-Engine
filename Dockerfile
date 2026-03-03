# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies for CasADi and other libs
RUN apt-get update && apt-get install -y --no-install-recommends 
    build-essential 
    liblapack-dev 
    libblas-dev 
    libf2c2-dev 
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Expose ports for FastAPI and Streamlit
EXPOSE 8000
EXPOSE 8501

# Command to run will be overridden by docker-compose
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

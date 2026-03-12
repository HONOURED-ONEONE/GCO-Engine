from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from services.kpi.routers.kpi import router as kpi_router

app = FastAPI(
    title="GCO KPI Ingestion Service",
    description="Standalone FastAPI microservice for KPI Ingestion",
    version="1.0.0"
)

allow_origins = os.getenv("ALLOW_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(kpi_router, prefix="/kpi", tags=["kpi"])

@app.get("/")
def root():
    return {"message": "kpi-service running"}

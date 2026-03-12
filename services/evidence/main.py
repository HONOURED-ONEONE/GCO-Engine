from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import evidence
import os

app = FastAPI(
    title="GCO Evidence & Reporting Service",
    description="Stage-5 Evidence/Reporting Service for GCO-Engine",
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

app.include_router(evidence.router)

@app.get("/")
async def root():
    return {"message": "evidence-service running"}

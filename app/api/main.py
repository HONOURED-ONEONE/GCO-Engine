"""
LEGACY MONOLITH (Retired)
-------------------------
This file and the app.api module are retained for archival and migration reference only.
The production GCO Engine now runs on a pure microservices stack (see services/*).
This component is NOT used in the production runtime as of the Final Cut-Over.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import mode, optimize, kpi, corridor, ot, policy, evidence, twin, pilot
from app.api.utils.io import init_files

app = FastAPI(title="GCO Engine (Phase 6 - Field Pilot Readiness)")

# Initialize data files on start
init_files()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mode.router, prefix="/mode", tags=["Mode"])
app.include_router(optimize.router, prefix="/optimize", tags=["Optimize"])
app.include_router(kpi.router, prefix="/kpi", tags=["KPI"])
app.include_router(corridor.router, prefix="/corridor", tags=["Corridor"])
app.include_router(ot.router, prefix="/ot", tags=["OT"])
app.include_router(policy.router, prefix="/policy", tags=["Policy"])
app.include_router(evidence.router, prefix="/evidence", tags=["Evidence"])
app.include_router(twin.router, prefix="/twin", tags=["Twin"])
app.include_router(pilot.router, prefix="/pilot", tags=["Pilot"])

@app.get("/")
async def root():
    return {"message": "GCO Engine Phase 6 - Field Pilot Readiness is running."}

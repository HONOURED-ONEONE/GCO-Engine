from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import mode, optimize, kpi, corridor
from app.api.utils.io import init_files

app = FastAPI(title="Golden Corridor Optimization Engine (Phase 1)")

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

@app.get("/")
async def root():
    return {"message": "GCO Engine API Phase 1 is running."}

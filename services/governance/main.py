from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.governance.routers import corridor, mode, governance
from services.governance.utils.io import init_files

app = FastAPI(title="Governance Control Plane")

init_files()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(corridor.router, prefix="/corridor", tags=["Corridor"])
app.include_router(mode.router, prefix="/mode", tags=["Mode"])
app.include_router(governance.router, prefix="/governance", tags=["Internal"])

@app.get("/")
async def root():
    return {"message": "Governance Service is running."}

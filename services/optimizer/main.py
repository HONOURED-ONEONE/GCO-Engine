from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.optimizer.routers.optimize import router

app = FastAPI(title="GCO Optimizer Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/optimize")

@app.get("/")
async def root():
    return {"message": "optimizer-service running"}

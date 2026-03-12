from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from .routers.policy import router
from services.policy.db.session import init_db

app = FastAPI(title="GCO Policy/MARL Service")

init_db()

allow_origins = os.getenv("ALLOW_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/policy", tags=["policy"])

@app.get("/")
def root():
    return {"message": "policy-service running"}

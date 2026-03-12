from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from .routers import llm

app = FastAPI(title="GCO LLM Reasoning Sidecar", description="Read-only LLM helper for explaining and validating proposals.")

origins = os.environ.get("ALLOW_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(llm.router, prefix="/llm")

@app.get("/")
def read_root():
    return {"message": "llm-service running"}

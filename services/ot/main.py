from fastapi import FastAPI
from .routers.ot import router

app = FastAPI(title="GCO OT Connector Service")

@app.get("/")
async def root():
    return {"message": "ot-service running"}

app.include_router(router)

from fastapi import FastAPI
from .routers.ot import router
from services.ot.db.session import init_db

app = FastAPI(title="GCO OT Connector Service")

init_db()

@app.get("/")
async def root():
    return {"message": "ot-service running"}

app.include_router(router)

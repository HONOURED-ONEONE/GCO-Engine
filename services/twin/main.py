from fastapi import FastAPI
from .routers import twin, pilot
from .utils.metrics import metrics_tracker

app = FastAPI(title="GCO Twin & Pilot Service", version="1.0.0")

@app.get("/")
async def root():
    return {
        "message": "twin-service running",
        "metrics": metrics_tracker.get_summary()
    }

app.include_router(twin.router, prefix="/twin", tags=["twin"])
app.include_router(pilot.router, prefix="/pilot", tags=["pilot"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)

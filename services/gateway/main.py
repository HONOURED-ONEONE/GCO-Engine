from fastapi import FastAPI
from .router import router

app = FastAPI(title="PEP Gateway")
app.include_router(router)

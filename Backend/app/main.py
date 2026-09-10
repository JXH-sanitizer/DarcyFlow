from fastapi import FastAPI
from app.api.v1.endpoints.model import router as model_router

app = FastAPI()

app.include_router(model_router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {"status": "ok"}

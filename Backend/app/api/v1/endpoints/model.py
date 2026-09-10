from app.schemas.model import ModelParams
from fastapi import APIRouter

router = APIRouter()
@router.post("/model/run")
def run_model(params: ModelParams):
  return params
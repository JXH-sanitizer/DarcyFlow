from app.schemas.model import ModelParams
from app.services.model_builder import ModelRunError, ModelTimeoutError, build_and_run_model
from fastapi import APIRouter, HTTPException

router = APIRouter()
@router.post("/model/run")
def run_model(params: ModelParams):
  try:
    result = build_and_run_model(params)
  except ModelTimeoutError as e:
    raise HTTPException(
      status_code=504,
      detail={
          "code": "MODEL_TIMEOUT",
          "message": f"模型计算超过 {e.timeout} 秒被中止。请缩小网格或减小单元尺寸比例悬殊。",
          "log_tail": "",
      },
    )
  except ModelRunError as e:
    raise HTTPException(
      status_code=400,
      detail={
          "code": "MODEL_RUN_ERROR",
          "message": "模型未收敛或求解失败，请检查参数设置。常见原因：缺少定水头边界、抽水强度超出含水层供水能力。",
          "log_tail": e.log_tail,
      },
    )
  return {
    "code": "SUCCESS",
    "message": "模型计算成功。",
    "result": result
  }
  

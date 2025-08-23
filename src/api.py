from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .async_pipeline import processor
from pathlib import Path
import torch


class ComputeRequest(BaseModel):
    year: int
    month: int


app = FastAPI()


@app.get("/health")
def health():
    try:
        device = (
            "cuda"
            if torch.cuda.is_available()
            else "mps" if torch.backends.mps.is_available() else "cpu"
        )
        model_path = Path(
            "models/DocLayout-YOLO-DocStructBench/doclayout_yolo_docstructbench_imgsz1024.pt"
        )
        if not model_path.exists():
            raise HTTPException(status_code=500, detail="Model file not found")
        return {"status": "healthy", "device": device}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/compute")
def compute(request: ComputeRequest):
    try:
        request_id = processor.start_computation(request.year, request.month)
        return {"request_id": request_id, "status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status/{request_id}")
def get_status(request_id: str):
    try:
        status = processor.get_status(request_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/result/{request_id}")
def get_result(request_id: str):
    try:
        result = processor.get_result(request_id)
        if result.get("status") == "not_found":
            raise HTTPException(status_code=404, detail="Result not found")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

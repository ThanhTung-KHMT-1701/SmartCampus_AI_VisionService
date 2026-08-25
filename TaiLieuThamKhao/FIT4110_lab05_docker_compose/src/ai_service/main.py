"""
Simple AI service mock for Lab 05.

This service exposes two endpoints:

* `GET /health` – returns status, service name and version.
* `POST /predict` – returns a dummy list of detected objects and confidences.

You can replace this file with your actual inference code (e.g. YOLOv8 model).
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

SERVICE_NAME = "ai-service"
SERVICE_VERSION = "0.5.0"

app = FastAPI(
    title="FIT4110 Lab 05 - AI Service",
    version=SERVICE_VERSION,
    description="Mock AI service used in Docker Compose stack.",
)


class Prediction(BaseModel):
    objects: List[str]
    confidence: List[float]


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": SERVICE_NAME, "version": SERVICE_VERSION}


@app.post("/predict", response_model=Prediction)
def predict() -> Prediction:
    # This dummy implementation always returns two objects
    return Prediction(objects=["person", "bicycle"], confidence=[0.98, 0.85])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
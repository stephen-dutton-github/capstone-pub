from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from tempfile import NamedTemporaryFile
from typing import Tuple
import shutil
import os
import uvicorn
import asyncio
import time

from xray_manager_v2  import ChestXRayClassifier

app = FastAPI()

# load application level, because it's slow to initiaize
classifier = ChestXRayClassifier(data_dir='/app/cxr/')
classifier.class_names = ['Covid', 'Normal', 'Pneumonia', 'Tuberculosis']
classifier.load_model('/app/chest_xray_model_v3.h5')

async def _do_heartbeat():
    # simulate I/O work
    await asyncio.sleep(0)
    return {"status": "ok", "ts": time.time()}

@app.get("/heartbeat")
async def heartbeat():
    return await _do_heartbeat()

@app.post("/predict")
async def predict_image(file: UploadFile = File(...)):
    if file.content_type not in ["image/jpg","image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Only JPEG or PNG files are supported.")

    try:
        # Save the file to a temporary location
        with NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[-1]) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        # Call the classifier

        predicted_class, confidence = classifier.predict(tmp_path)

        # Clean up
        os.remove(tmp_path)

        return JSONResponse(content={
            "predicted_class": predicted_class,
            "confidence": round(float(confidence), 4)
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

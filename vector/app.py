import sqlite3
from dataclasses import asdict
from typing import Any
from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse
from api.services.patient_services import PatientServices, Patient
from api.services.patient_services import Patient, Admission
from api.services.notes_manager import NotesManager
from api.services.embedding_manager import EmbeddingManager
from api.services.diagnosis_manager import DiagnosisManager
from typing_extensions import Annotated
from pydantic import BaseModel
import re
from fastapi import HTTPException
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List
import os, base64
import uvicorn
from fastapi.responses import Response 

app = FastAPI()

class SearchRequest(BaseModel):
    """
    Schema for search requests.
    
    Attributes:
        query (str): The search query string.
        result_set_size (int): The number of results to return. Defaults to 1.
    """
    query: str
    result_set_size: int = 1

class SubjectRequest(BaseModel):
    """
    Schema for requests that require a single subject ID.
    
    Attributes:
        subject_id (str): The unique identifier for a subject.
    """
    subject_id: str

class PatientNameRequest(BaseModel):
    """
    Schema for requests that require a patient's first and last name prefixes.
    
    Attributes:
        first_name (str): The first name prefix of the patient.
        last_name (str): The last name prefix of the patient.
    """
    first_name: str
    last_name: str

class DiagnosisRequest(BaseModel):
    """
    Schema for diagnosis-related requests.
    
    Attributes:
        first_name (str): The first name prefix of the patient.
        last_name (str): The last name prefix of the patient.
        multi_modal (bool): Whether to use multi-modal diagnosis.
    """
    first_name: str
    last_name: str
    multi_modal: bool

class ConditionRequest(BaseModel):
    """
    Schema for condition search requests.
    
    Attributes:
        query (str): The search query string.
        result_set_size (int): The number of results to return. Defaults to 1.
    """
    query: str
    result_set_size: int = 1

def get_db_base():
    """
    Retrieve the database path from the environment variable `MIMICIV_DB_PATH`.
    
    Returns:
        str: The path to the database.
    """
    return os.getenv("MIMICIV_DB_PATH")
# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

from fastapi import HTTPException, status

@app.post("/condition_search", response_class=JSONResponse)
async def condition_search(request: ConditionRequest) -> list[Patient]:
    """Return all text notes for the given *subject_id*."""
    embedding_url = os.environ.get("EMBEDDING_SERVICE_URL")
    if not embedding_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Missing EMBEDDING_SERVICE_URL in environment."
        )

    try:
        svc = EmbeddingManager(
            embedding_service_url=embedding_url,
            embeddings_created=True
        )

        result_ids = svc.query_admissions_embeddings(
            query=request.query,
            result_set_size=request.result_set_size
        ).get("ids", [[]])[0]

        subject_ids = {sid.split('.')[0] for sid in result_ids}

        with PatientServices(get_db_base()) as patient_svc:
            return [
                p for p in patient_svc.patients()
                if str(p.subject_id) in subject_ids
            ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Condition search failed: {str(e)}"
        )



@app.post("/diagnose", response_class=JSONResponse)
async def diagnose(request: DiagnosisRequest):
    """Return subject_id(s) whose first & family names match the supplied prefixes."""
    try:
        svc = DiagnosisManager()
        diagnosis = await svc.get_diagnosis_report(first_name=request.first_name, 
                                                   last_name=request.last_name, 
                                                   multi_modal=request.multi_modal)
        unredacted = (
            "subject_id",
            "anonymized_prompt",
            "cnn_diagnosis",
            "cnn_confidence",
            "icd_code",
            "icd_version",
            "icd_diagnosis",
            "llm_diagnosis",
            "multi_modal",
            "llm_correct",
            "cnn_correct"
        )
        
        mapped_diagnosis_report = {k: diagnosis[k] for k in unredacted}
        img_url = f"http://localhost:8080/xray_image/{mapped_diagnosis_report["subject_id"]}"
        mapped_diagnosis_report["xray_url"] = img_url
        return mapped_diagnosis_report
    
    
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/notes", response_class=JSONResponse)
async def fetch_notes(request: SubjectRequest) -> dict[str, str]:
    """Return all text notes for the given *subject_id*."""
    try:
        # PatientServices is a synchronous context manager
        with PatientServices(get_db_base()) as svc:
            notes = await svc.get_notes(subject_id=request.subject_id)
            return notes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/subject_id", response_class=JSONResponse)
def get_subject_id(request: PatientNameRequest) -> Any:
    """Return subject_id(s) whose first & family names match the supplied prefixes."""
    try:
        with PatientServices(get_db_base()) as svc:
            ids = svc.get_subject_id(first_name=request.first_name, last_name=request.last_name)
            return ids
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/xray_image/{subject_id}", response_class=Response)
async def get_xray_image(subject_id: str) -> Response:
    """
    Return (binary) JPEG data of the first x-ray image for *subject_id*.

    The browser receives a normal `image/jpeg` response, so
    navigating to /xray_image/123456 opens the picture directly.
    """
    try:
        with PatientServices(get_db_base()) as svc:
            # Re-use your existing helper that already fetches the bytes
            xrays = await svc.get_xrays(subject_id=subject_id)
            if not xrays:
                raise HTTPException(status_code=404, detail="No x-ray found")

            # Take the first image in the dict.  You could also accept an
            # extra path parameter (filename) if you want finer control.
            _, img_bytes = next(iter(xrays.items()))

            return Response(
                content=img_bytes,
                media_type="image/jpeg",
                headers={"Content-Disposition": f'inline; filename="{subject_id}.jpg"'}
            )

    except HTTPException:          # bubble up 404, 500, etc. unchanged
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/xrays", response_class=JSONResponse)
async def fetch_xrays(request: SubjectRequest) -> dict[str, str]:
    """Return base-64-encoded x-ray JPEGs for the given *subject_id*."""
    try:
        with PatientServices(get_db_base()) as svc:
            xrays_bytes = await svc.get_xrays(subject_id=request.subject_id)
            # JSON cannot transport raw bytes; encode to base64 → UTF-8 str
            encoded = {fname: base64.b64encode(data) for fname, data in xrays_bytes.items()}
            return encoded
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/icds", response_class=JSONResponse)
def get_subject_id(request: SubjectRequest) -> Any:
    """Return subject_id(s) whose first & family names match the supplied prefixes."""
    try:
        with PatientServices(get_db_base()) as svc:
            ids = svc.get_icds(subject_id=request.subject_id)
            return ids
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/subject_id", response_class=JSONResponse)
def get_subject_id(request: PatientNameRequest) -> Any:
    """Return subject_id(s) whose first & family names match the supplied prefixes."""
    try:
        with PatientServices(get_db_base()) as svc:
            ids = svc.get_subject_id(first_name=request.first_name, last_name=request.last_name)
            return ids
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admissions", response_class=JSONResponse)
def get_admissions() -> list[Admission]:
    try:
        with PatientServices(get_db_base()) as patients:
            return patients.get_admissions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/patients", response_class=JSONResponse)
def get_patients() -> list[Patient]:
    try:
        with PatientServices(get_db_base()) as patients:
            return patients.patients()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/subject_ids", response_class=JSONResponse)
def get_subject_ids() -> list[str]:
    try:
        with PatientServices(get_db_base()) as patients:
            return patients.get_subject_ids()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Run the FastAPI app. By default, it listens on 127.0.0.1:8000
    # Adjust host/port as needed.
    uvicorn.run(app, host="0.0.0.0", port=8000)
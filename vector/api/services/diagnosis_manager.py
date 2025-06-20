from langgraph.graph import StateGraph, END
from typing import TypedDict, Callable, Awaitable, List, Dict
from dataclasses import dataclass, asdict, fields
from enum import Enum
from .patient_services import PatientServices
from .diagnosis_graph import DiagnosisGraph, DiagnosisState, StateKey
from datetime import datetime
import requests
import asyncio
import re
import json
import os
from ..app import get_db_base
  
class DiagnosisManager:
    """
    Manages the diagnosis workflow across patients using the DiagnosisGraph.

    This class serves as a higher-level coordinator that initializes and manages the execution 
    of diagnosis graphs, which handle detailed logic for patient data processing, LLM queries, 
    and multimodal (text + x-ray) diagnostic reasoning.

    It provides a simplified interface to trigger diagnoses for individual patients, with 
    support for emitting status events during processing.
    """

    def __init__(self) -> None:
        """
        Initialize the DiagnosisManager.

        Environment variables must be defined to configure the required service endpoints:
        - XRAY_PREDICTION_URL: URL of the x-ray diagnostic service.
        - LLM_SERVICE_URL: URL of the LLM function calling service.
        """
        self.xray_prediction_url = os.environ.get("XRAY_PREDICTION_URL")
        self.llm_service_url = os.environ.get("LLM_SERVICE_URL")

    @staticmethod
    async def default_event_emitter(event: str) -> None:
        """
        Default event emitter that prints events to the console.

        This is used when no custom event emitter is provided to log the progress of the diagnosis.

        Args:
            event (str): The event message to be emitted.
        """
        print(event)


    async def get_diagnosis_report_sid(self,
                                     subject_id: str,
                                     multi_modal: bool = True,
                                     event_emitter = default_event_emitter) -> DiagnosisState:
        """
        Generates a diagnosis report for a patient using their subject ID.

        This method first retrieves the patient's first and last name using their subject ID,
        then initializes a DiagnosisGraph, runs it asynchronously, and returns 
        the final diagnosis state including LLM and optional x-ray based diagnoses.

        Args:
            subject_id (str): The patient's subject ID.
            multi_modal (bool, optional): If True, includes x-ray analysis in the diagnostic process.
                                          Defaults to True.
            event_emitter (Callable, optional): An async callback function used to emit status updates.
                                                Defaults to `default_event_emitter`.

        Returns:
            DiagnosisState: The final state returned from the DiagnosisGraph execution,
                            containing diagnostic outcomes and related metadata.
        """
        
        # Get patient's first and last name from subject ID
        with PatientServices(get_db_base()) as ps:
            patient = ps.get_patient_by_subject_id(subject_id)
            if not patient:
                raise ValueError(f"No patient found with subject ID {subject_id}")
            first_name = patient["first_name"]
            last_name = patient["last_name"]
        
        diagnosis_graph = DiagnosisGraph(
            xray_prediction_url=self.xray_prediction_url,
            llm_service_url=self.llm_service_url,
            multi_modal=multi_modal,
            __event_emitter__=event_emitter)
        
        graph_result = {}
        try:
            graph_result = await diagnosis_graph.run(first_name, last_name)
            
        except Exception as exc:
            print(exc.with_traceback)

        return graph_result

    async def get_diagnosis_report(self, 
                                   first_name: str, 
                                   last_name: str, 
                                   multi_modal = True,
                                   event_emitter = default_event_emitter) -> DiagnosisState:
        """
        Generates a diagnosis report for a patient.

        This method initializes a DiagnosisGraph, runs it asynchronously, and returns 
        the final diagnosis state including LLM and optional x-ray based diagnoses.

        Args:
            first_name (str): The patient's first name.
            last_name (str): The patient's last name.
            multi_modal (bool, optional): If True, includes x-ray analysis in the diagnostic process.
                                          Defaults to True.
            event_emitter (Callable, optional): An async callback function used to emit status updates.
                                                Defaults to `default_event_emitter`.

        Returns:
            DiagnosisState: The final state returned from the DiagnosisGraph execution,
                            containing diagnostic outcomes and related metadata.
        """
        
        diagnosis_graph = DiagnosisGraph(
            xray_prediction_url=self.xray_prediction_url,
            llm_service_url=self.llm_service_url,
            multi_modal=multi_modal,
            __event_emitter__= event_emitter)
        
        graph_result = {}
        try:
            graph_result = await diagnosis_graph.run(first_name, last_name)
            
        except Exception as exc:
            print(exc.with_traceback)

        return graph_result




if __name__ == "__main__":
    
    async def diagnose_all() -> tuple[list[DiagnosisState], list[DiagnosisState]] :
        import csv
        patients = []
        with PatientServices(os.getenv("MIMICIV_DB_PATH")) as ps:
            patients =  ps.patients()
        
        dm = DiagnosisManager()
        diagnosis_llm_only = []
        diagnosis_with_xray = []
        for p in patients:
            diag_llm = await dm.get_diagnosis_report(first_name=p.first_name, 
                                                     last_name=p.family_name,
                                                     multi_modal=False)
            
            diag_xray = await dm.get_diagnosis_report(first_name=p.first_name, 
                                                      last_name=p.family_name,
                                                      multi_modal=True)
            diagnosis_llm_only.append(diag_llm)
            diagnosis_with_xray.append(diag_xray)
        

        with open(f"/app/api/services/diagnoses/diagnoses_{str(datetime.now().timestamp())}.txt", "w") as f:
            
            fieldnames= list(StateKey)

            redacted = [StateKey.ANONYMIZED_PROMPT,
                        StateKey.FINAL_PROMPT,
                        StateKey.COMBINED_PROMPT,
                        StateKey.ADMISSION_NOTES,
                        StateKey.XRAY_IMAGES,
                        StateKey.FIRST_NAME,
                        StateKey.LAST_NAME]

            [fieldnames.remove(item) for item in redacted]

            writer = csv.DictWriter(f,fieldnames=fieldnames,extrasaction="ignore")
            writer.writeheader()
            writer.writerows(diagnosis_llm_only)
            writer.writerows(diagnosis_with_xray)

        return diagnosis_llm_only,diagnosis_with_xray
    
    llm_only, xray_diags = asyncio.run(diagnose_all())

    [print(d) for d in llm_only]
    print("--------------")
    [print(d) for d in xray_diags]

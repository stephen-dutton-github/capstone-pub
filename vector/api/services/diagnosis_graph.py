from langgraph.graph import StateGraph, END
from typing import TypedDict, Callable, Awaitable, List, Dict, Final, Any
from dataclasses import dataclass, asdict
from enum import Enum
from .patient_services import PatientServices
from .llm_dispatcher import LLMDispatcher, DispatcherClient
from datetime import datetime
import textwrap
import requests
import asyncio
import re
import json
import os

def get_db_base():
    """
    Retrieve the database base path from the environment variable.

    Returns:
        str: The database base path.
    """
    return os.getenv("MIMICIV_DB_PATH")

# Enumeration for state keys to avoid typos
class StateKey(str, Enum):
    """
    Enumeration for state keys used in the diagnosis graph to avoid typos.
    """
    ADMISSION_NOTES   = "admission_notes"
    ANONYMIZED_PROMPT = "anonymized_prompt"
    CNN_CONFIDENCE    = "cnn_confidence"
    CNN_CORRECT       = "cnn_correct"
    CNN_DIAGNOSIS     = "cnn_diagnosis"
    COMBINED_PROMPT   = "combined_prompt"
    FINAL_PROMPT      = "final_prompt"
    FIRST_NAME        = "first_name"
    ICD_CODE          = "icd_code"
    ICD_DIAGNOSIS     = "icd_diagnosis"
    ICD_VERSION       = "icd_version"
    LAST_NAME         = "last_name"
    LLM_CORRECT       = "llm_correct"
    LLM_DIAGNOSIS     = "llm_diagnosis"
    MULTI_MODAL       = "multi_modal"
    SUBJECT_ID        = "subject_id"
    XRAY_IMAGES       = "xray_images"


# Define the state structure for the graph
class DiagnosisState(TypedDict):
    """
    Typed dictionary representing the state passed between graph nodes.

    Attributes:
        admission_notes (List[str]): List of admission notes.
        multi_modal (str): Multi-modal status.
        anonymized_prompt (str): Anonymized prompt text.
        cnn_confidence (str): Confidence score from CNN diagnosis.
        cnn_diagnosis (str): Diagnosis result from CNN.
        cnn_correct (str): Flag indicating if CNN diagnosis is correct.
        combined_prompt (str): Combined prompt text.
        llm_correct (str): Flag indicating if LLM diagnosis is correct.
        llm_diagnosis (str): Diagnosis result from LLM.
        final_prompt (str): Final prompt text.
        first_name (str): Patient's first name.
        last_name (str): Patient's last name.
        subject_id (str): Patient's subject ID.
        xray_images (List[str]): List of x-ray image paths.
        icd_version (str): ICD version.
        icd_code (str): ICD code.
        icd_diagnosis (str): ICD diagnosis description.
    """
    admission_notes: List[str]
    multi_modal : str
    anonymized_prompt: str
    cnn_confidence: str
    cnn_diagnosis: str
    cnn_correct : str
    combined_prompt: str
    llm_correct: str
    llm_diagnosis: str
    final_prompt: str
    first_name: str
    last_name: str
    subject_id: str
    xray_images: List[str]
    icd_version: str
    icd_code :str
    icd_diagnosis: str


class DiagnosisGraph(DispatcherClient):
    """
    Neuro-symbolic patient diagnosis graph.

    Attributes:
        xray_prediction_url (str): URL for x-ray prediction service.
        llm_service_url (str): URL for LLM service.
        multi_modal (bool): Flag indicating if multi-modal processing is enabled.
        __event_emitter__ (Callable[[str], Awaitable[None]]): Event emitter for logging.
        dispatcher (LLMDispatcher): Dispatcher for LLM service.
        graph (StateGraph): State graph for diagnosis workflow.
    """
 
    def __init__(
        self,
        xray_prediction_url: str,
        llm_service_url: str,
        multi_modal: bool = True,
        __event_emitter__: Callable[[str], Awaitable[None]] = None):
        """
        Initialize the DiagnosisGraph.

        Args:
            xray_prediction_url (str): URL for x-ray prediction service.
            llm_service_url (str): URL for LLM service.
            multi_modal (bool): Enable multi-modal processing. Defaults to True.
            __event_emitter__ (Callable[[str], Awaitable[None]]): Event emitter for logging. Defaults to None.
        """
        self.xray_prediction_url = xray_prediction_url
        self.llm_service_url = llm_service_url
        self.multi_modal = multi_modal
        self.__event_emitter__ = __event_emitter__

        self.dispatcher = LLMDispatcher(
            llm_service_url=self.llm_service_url,
            client=self,
            event_emitter=self.__event_emitter__
        )

        self.graph = self.build_graph()

    def get_function_registry(self):
        """
        Retrieve the function registry for the graph.

        Returns:
            dict: A dictionary mapping function names to their implementations.
        """
        return {
            "llm_diagnosis" : self.llm_diagnosis,
            "llm_performance" : self.llm_performance
        }
    
    def get_model(self):
        return os.environ.get("OLLAMA_DEFAULT_MODEL")

    def llm_diagnosis(self, 
                      state:DiagnosisState,
                      subject_id:str, 
                      condition:str) -> None:
        """
        Update the state with the LLM diagnosis.

        Args:
            state (DiagnosisState): Current state of the graph.
            subject_id (str): Patient's subject ID.
            condition (str): Diagnosis condition.
        """
        state[StateKey.LLM_DIAGNOSIS] = condition

    def llm_performance(self, 
                       state:DiagnosisState,
                       llm_correct:str, 
                       cnn_correct:str) -> None:
        """
        Update the state with LLM and CNN performance flags.

        Args:
            state (DiagnosisState): Current state of the graph.
            llm_correct (str): Flag indicating if LLM diagnosis is correct.
            cnn_correct (str): Flag indicating if CNN diagnosis is correct.
        """
        state[StateKey.LLM_CORRECT] = llm_correct
        state[StateKey.CNN_CORRECT] = cnn_correct

    def build_graph(self) -> StateGraph:
        """
        Build the state graph for the diagnosis workflow.

        Returns:
            StateGraph: Compiled state graph.
        """
        builder = StateGraph(DiagnosisState)
        # Add nodes
        builder.add_node("set_multi_modal_status",self.set_multi_modal_status)
        builder.add_node("resolve_subject_id", self.resolve_subject_id)
        builder.add_node("get_admission_notes", self.get_admission_notes)
        if self.multi_modal:
            builder.add_node("get_xrays", self.get_xrays)
            builder.add_node("diagnose_xrays", self.diagnose_xrays)
        builder.add_node("combine_prompt", self.combine_prompt)
        builder.add_node("anonymize_prompt", self.anonymize_prompt)
        builder.add_node("retrieve_llm_diagnosis", self.retrieve_llm_diagnosis)
        builder.add_node("retreive_icd", self.retreive_icd)
        builder.add_node("assess_llm_performance", self.assess_llm_performance)

        # Entry point
        builder.set_entry_point("set_multi_modal_status")
        
        # Edges
        builder.add_edge("set_multi_modal_status","resolve_subject_id")
        builder.add_edge("resolve_subject_id", "get_admission_notes")
        if self.multi_modal:
            builder.add_edge("get_admission_notes", "get_xrays")
            builder.add_edge("get_xrays", "diagnose_xrays")
            builder.add_edge("diagnose_xrays", "combine_prompt")
        else:
            builder.add_edge("get_admission_notes", "combine_prompt")
        builder.add_edge("combine_prompt", "anonymize_prompt")
        builder.add_edge("anonymize_prompt", "retrieve_llm_diagnosis")
        builder.add_edge("retrieve_llm_diagnosis", "retreive_icd")
        builder.add_edge("retreive_icd", "assess_llm_performance")
        builder.add_edge("assess_llm_performance", END)
        return builder.compile()

    async def set_multi_modal_status(self, state: DiagnosisState) -> DiagnosisState:    
        """
        Set the multi-modal status in the state.

        Args:
            state (DiagnosisState): Current state of the graph.

        Returns:
            DiagnosisState: Updated state.
        """
        if self.__event_emitter__:
            await self.__event_emitter__("Mapping multi_modal parameter...")
        
        state[StateKey.MULTI_MODAL] = "true" if self.multi_modal else "false"
        return state

    async def resolve_subject_id(self, state: DiagnosisState) -> DiagnosisState:
        """
        Resolve the subject ID based on the patient's name.

        Args:
            state (DiagnosisState): Current state of the graph.

        Returns:
            DiagnosisState: Updated state with subject ID.
        """
        if self.__event_emitter__:
            await self.__event_emitter__("Resolving subject ID...")

        with PatientServices(get_db_base()) as ps:
            subject_id = ps.get_subject_id(first_name=state[StateKey.FIRST_NAME],
                                        last_name=state[StateKey.LAST_NAME])[0]
            state[StateKey.SUBJECT_ID] = str(subject_id["subject_id"])

        return state

    async def get_admission_notes(self, state: DiagnosisState) -> DiagnosisState:
        """
        Fetch admission notes for the patient.

        Args:
            state (DiagnosisState): Current state of the graph.

        Returns:
            DiagnosisState: Updated state with admission notes.
        """
        if self.__event_emitter__:
            await self.__event_emitter__("Fetching admission notes...")

        with PatientServices(get_db_base()) as ps:
            state[StateKey.ADMISSION_NOTES] = await ps.get_notes(subject_id=state[StateKey.SUBJECT_ID])
        return state

    async def get_xrays(self, state: DiagnosisState) -> DiagnosisState:
        """
        Fetch x-ray images for the patient.

        Args:
            state (DiagnosisState): Current state of the graph.

        Returns:
            DiagnosisState: Updated state with x-ray images.
        """
        if self.__event_emitter__:
            await self.__event_emitter__("Fetching x-rays...")

        with PatientServices(get_db_base()) as ps:
            state[StateKey.XRAY_IMAGES] = await ps.get_xrays(subject_id=state[StateKey.SUBJECT_ID])
        return state

    async def diagnose_xrays(self, state: DiagnosisState) -> DiagnosisState:
        """
        Perform diagnosis on x-ray images.

        Args:
            state (DiagnosisState): Current state of the graph.

        Returns:
            DiagnosisState: Updated state with CNN diagnosis and confidence.
        """
        import base64, io, requests as _req
        if self.__event_emitter__:
            await self.__event_emitter__("Diagnosing x-rays...")

        diagnoses: Dict = {}
        for key in state[StateKey.XRAY_IMAGES]:
            binary = state[StateKey.XRAY_IMAGES][key]
            file_obj = io.BytesIO(binary)
            files = {"file": (key, file_obj, "image/jpeg")}
            try:
                resp = _req.post(self.xray_prediction_url, files=files)
                resp.raise_for_status()
                diagnoses = resp.json()
            except _req.RequestException as exc:
                raise RuntimeError(f"X-ray diagnosis failed for {key}: {exc}") from exc
        state[StateKey.CNN_DIAGNOSIS] = diagnoses["predicted_class"]
        state[StateKey.CNN_CONFIDENCE] = diagnoses["confidence"]

        return state

    async def combine_prompt(self, state: DiagnosisState) -> DiagnosisState:
        """
        Combine admission notes and x-ray diagnosis into a single prompt.

        Args:
            state (DiagnosisState): Current state of the graph.

        Returns:
            DiagnosisState: Updated state with combined prompt.
        """
        if self.__event_emitter__:
            await self.__event_emitter__("Combining prompt...")
        notes = state[StateKey.ADMISSION_NOTES]
        combined = []
        if self.multi_modal:
            cnn_diagnosis = state[StateKey.CNN_DIAGNOSIS]
            cnn_confidence = state[StateKey.CNN_CONFIDENCE]

            for n, d in zip(notes, cnn_diagnosis):
                combined = """Admission Note: {note_name}

                {note_content}
                
                Diagnosis: an x-rays diagnosis of {cnn_diagnosis} with {cnn_confidence} percent confidence was also provided.
                """.format(note_name=n,
                           note_content=notes[n],
                           cnn_diagnosis=cnn_diagnosis,
                           cnn_confidence=cnn_confidence)

        else:
            combined = "\n".join(f"Admission Note: ({n})\n{notes[n]}\n" for n in notes)

        state[StateKey.COMBINED_PROMPT] = combined
        return state

    async def anonymize_prompt(self, state: DiagnosisState) -> DiagnosisState:
        """
        Anonymize the combined prompt by removing patient identifiers.

        Args:
            state (DiagnosisState): Current state of the graph.

        Returns:
            DiagnosisState: Updated state with anonymized prompt.
        """
        if self.__event_emitter__:
            await self.__event_emitter__("Anonymizing prompt...")
        text = state[StateKey.COMBINED_PROMPT]
        fname = state[StateKey.FIRST_NAME]
        lname = state[StateKey.LAST_NAME]
        text = re.sub(re.escape(f"{fname} {lname}"), "[ANONYMIZED]", text, flags=re.IGNORECASE)
        text = re.sub(re.escape(fname), "[ANONYMIZED]", text, flags=re.IGNORECASE)
        text = re.sub(re.escape(lname), "[ANONYMIZED]", text, flags=re.IGNORECASE)
        state[StateKey.ANONYMIZED_PROMPT] = text
        return state

    async def retrieve_llm_diagnosis(self, state: DiagnosisState) -> DiagnosisState:
        """
        Retrieve diagnosis from the LLM service.

        Args:
            state (DiagnosisState): Current state of the graph.

        Returns:
            DiagnosisState: Updated state with LLM diagnosis.
        """
        
        prompt = f"""
        Consider ALL the following patient data:

        --- PATIENT DATA STARTS HERE ---

        {state[StateKey.ANONYMIZED_PROMPT]}

        --- PATIENT DATA ENDS HERE ---

        Now provide ONLY a JSON object:
        {{
            "function_name" : "llm_diagnosis",
            "arguments":{{
                "subject_id": "{state[StateKey.SUBJECT_ID]}",
                "condition": "..."
                }}
        }}

        'condition' only one of the followng conditions:
            -Covid-19
            -Pneumonia
            -Tuberculosis
            -Other

        IMPORTANT: ONLY RETURN the JSON object.
        """

        state[StateKey.FINAL_PROMPT] = prompt

        if self.__event_emitter__:
            await self.__event_emitter__("Running LLM Diagnosis...")

        await self.dispatcher.run(state, state[StateKey.FINAL_PROMPT])

        return state

    async def retreive_icd(self, state: DiagnosisState) -> DiagnosisState:
        """
        Retrieve ICD codes and diagnosis for the patient.

        Args:
            state (DiagnosisState): Current state of the graph.

        Returns:
            DiagnosisState: Updated state with ICD data.
        """
        if self.__event_emitter__:
            await self.__event_emitter__("Retrieving ICD codes and pathology...")
        
        subject_id = state[StateKey.SUBJECT_ID]

        with PatientServices(get_db_base()) as ps:
            state[StateKey.ICD_CODE] = ps.get_icds(subject_id)[0]["icd_code"]
            state[StateKey.ICD_VERSION] = ps.get_icds(subject_id)[0]["icd_version"]
            state[StateKey.ICD_DIAGNOSIS] = ps.get_icds(subject_id)[0]["long_title"]
        
        return state

    async def assess_llm_performance(self, state: DiagnosisState) -> DiagnosisState:
        """
        Compare CNN / LLM diagnoses with the ground-truth ICD label.
        Guarantees that only a valid JSON object is parsed; all other text
        produced by the LLM is discarded.

        Args:
            state (DiagnosisState): Current state of the graph.

        Returns:
            DiagnosisState: Updated state with performance flags.
        """
        if self.__event_emitter__:
            await self.__event_emitter__("Comparing LLM and original (ICD) Diagnosis...")

        # ----------------------------------------------------------------─
        # 1. Build the grading prompt
        # -----------------------------------------------------------------
        value_set = {
            "fn" : "llm_performance",
            "cnn_diagnosis" : state[StateKey.CNN_DIAGNOSIS],
            "llm_diagnosis" : state[StateKey.LLM_DIAGNOSIS],
            "icd_diagnosis" : state[StateKey.ICD_DIAGNOSIS]
            }
        

        prompt_template = """
        REPLY ONLY WITH A JSON object of the following structure:
        {{
            "function_name" : "{fn}",
            "arguments":{{
                "llm_correct": "...",
                "cnn_correct": "..."
            }}
        }}

        Where:

        'llm_correct' is 'True' if {llm_diagnosis} can be considered
        a similar, or linked disorder to {icd_diagnosis}, otherwise 'False'.

        'cnn_correct' is 'True' if:
            · {cnn_diagnosis} can be medically considered a similar, or linked disorder to {icd_diagnosis}, otherwise 'False'.
            · {cnn_diagnosis} is 'Other' AND {icd_diagnosis} is a NON-PULMONARY disorder.

        IMPORTANT: Only return the JSON object
        """
        
        try:
            prompt_template  = textwrap.dedent(prompt_template)
            prompt = prompt_template.format(**value_set)
            await self.dispatcher.run(state, prompt)

        except Exception as exc:
            if self.__event_emitter__:
                await self.__event_emitter__(f"Error while executing LLM: {exc.__class__.__name__}: {exc}")
            raise

        return state
      

    async def run(self, first_name: str, last_name: str) -> dict:
        """
        Execute the diagnosis graph for a patient.

        Args:
            first_name (str): Patient's first name.
            last_name (str): Patient's last name.

        Returns:
            dict: Final state of the graph after execution.
        """
        initial_state = {

            # identity & lookup
            StateKey.MULTI_MODAL:      "false",
            StateKey.FIRST_NAME:       first_name,
            StateKey.LAST_NAME:        last_name,
            StateKey.SUBJECT_ID:       "-1",

            # raw inputs
            StateKey.ADMISSION_NOTES:  ["None"],
            StateKey.XRAY_IMAGES:      [""],

            # prompts
            StateKey.ANONYMIZED_PROMPT: "None",
            StateKey.COMBINED_PROMPT:   "None",
            StateKey.FINAL_PROMPT:      "None",

            # model outputs / scores
            StateKey.CNN_DIAGNOSIS:    "Other",
            StateKey.CNN_CONFIDENCE:   "0.0",
            StateKey.LLM_DIAGNOSIS:    "None",

            # ground‑truth ICD data
            StateKey.ICD_CODE:         "None",
            StateKey.ICD_VERSION:      "0",
            StateKey.ICD_DIAGNOSIS:    "None",

            # evaluation flags
            StateKey.CNN_CORRECT:      "False",
            StateKey.LLM_CORRECT:      "False",
        }

        final_state = await self.graph.ainvoke(initial_state)
        return final_state


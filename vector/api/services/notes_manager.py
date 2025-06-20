import os
import ollama
import pandas as pd
from api.services.patient_services import PatientServices
from chromadb import PersistentClient
from chromadb.api import QueryResult
import spacy


class NotesManager:
    """
    Manages the creation of hospital admission notes for patients.
    """

    def __init__(self, ollama_host: str, /, notes_created=False):
        """
        Initializes the NotesManager.

        Args:
            ollama_host (str): The host URL for the Ollama service.
            notes_created (bool): Flag indicating if notes have already been created.
        """
        self.ollama_model = os.environ.get("OLLAMA_DEFAULT_MODEL")
        self.db_base = os.getenv("MIMICIV_DB_PATH")
        self.ollama_host = ollama_host
        self.notes_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notes", "")
        self.notes_created = notes_created

    def create_all_notes(self) -> bool:
        """
        Creates hospital admission notes for all patients.

        Returns:
            bool: True if notes are successfully created or already exist, False otherwise.
        """
        if self.notes_created:
            return True

        baseline_prompt = """
            You are a hospital admissions notes generator.

            The note should contain between 200 to 300 words, in PLAIN text with no Markdown formatting.

            Relate the admission note to the following patient:
            - Patient ID: {subject_id}
            - Admission ID: {hospital_adm_id}
            - Patient Name: {patient_name}
            - Patient Age: {patient_age}
            
            The note should indicate conditions consistent with the following condition: {condition}, 
            but NOT state the condition directly.

            Structure the admission note with the EXACT following sections:
            - Patient Information
            - Initial Diagnosis
            - History of Present Illness (HPI)
            - Past Medical History (PMH)
            - Medications
            - Family History (FH)
            - Social History (SH)
            - Physical Examination (PE)
            - Initial Diagnosis
            - Plan (Treatment & Management)
        """

        admissions = []
        with PatientServices(self.db_base) as patients:
            
            admissions = patients.get_admissions()

        for admission in admissions:
            current_prompt = baseline_prompt.format(
                subject_id=admission.subject_id,
                patient_name=f"{admission.first_name} {admission.family_name}",
                hospital_adm_id=admission.hadm_id,
                patient_age=admission.anchor_age,
                condition=admission.long_title
            )

            client = ollama.Client(host=self.ollama_host)
            response = client.chat(model=self.ollama_model, messages=[{"role": "user", "content": current_prompt}])
            response_text = response["message"]["content"].replace("*", "").replace("#", "")

            note_name = os.path.join(self.notes_dir, f"{admission.subject_id}_{admission.hadm_id}.txt")
            os.makedirs(os.path.dirname(note_name), exist_ok=True)

            with open(note_name, "w") as f:
                f.write(response_text)

            print(f"Note {note_name} = {admission.icd_code}, version {admission.icd_version}")

        print("All notes have been created")
        self.notes_created = True
        return self.notes_created


if __name__ == "__main__":
    ollama_url = f"http://host.docker.internal:{os.getenv('OLLAMA_BASE_PORT', 11440)}"
    notes_generator = NotesManager(ollama_url, notes_created=True)
    notes_generator.create_all_notes()

    embedding_generator = EmbeddingManager(ollama_url, embeddings_created=False)
    if embedding_generator.create_all_embeddings():
       result = embedding_generator.query_admissions_embeddings("patients with breathing difficulty", 200)
       for metadata in result["metadatas"]:
           print(f"Results of query:\n{metadata}")


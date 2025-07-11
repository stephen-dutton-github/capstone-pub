import os
import ollama
import pandas as pd
from api.services.patient_services import PatientServices
from chromadb import PersistentClient
from chromadb.api import QueryResult
import spacy


class NotesManager:
    """
    Legacy test tool for creating hospital admission notes
    """

    def __init__(self, ollama_host: str, /, notes_created=False):
       ...

    def create_all_notes(self) -> bool:
      ...


if __name__ == "__main__":
    ollama_url = f"http://host.docker.internal:{os.getenv('OLLAMA_BASE_PORT', 11440)}"
    notes_generator = NotesManager(ollama_url, notes_created=True)
    notes_generator.create_all_notes()

    embedding_generator = EmbeddingManager(ollama_url, embeddings_created=False)
    if embedding_generator.create_all_embeddings():
       result = embedding_generator.query_admissions_embeddings("patients with breathing difficulty", 200)
       for metadata in result["metadatas"]:
           print(f"Results of query:\n{metadata}")


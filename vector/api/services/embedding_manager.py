import os
import json
import ollama
import pandas as pd
import requests
from api.services.patient_services import PatientServices
from chromadb import PersistentClient
from chromadb.api import QueryResult
import spacy


class EmbeddingManager:
    """
    Manages the creation and querying of embeddings for patient admission notes.
    """

    def __init__(self, 
                 embedding_service_url: str, 
                 embeddings_created=False, 
                 admissions_collection_name="admission_notes"):
        """
        Initializes the EmbeddingManager.

        Args:
            ollama_host (str): The host URL for the Ollama service.
            embeddings_created (bool): Flag indicating if embeddings have already been created.
            admissions_collection_name (str): Name of the collection for storing embeddings.
        """
        self.embedding_model = os.environ.get("OLLAMA_DEFAULT_MODEL")
        self.chroma_base = os.getenv("CHROMA_DB_PATH")
        self.embedding_service_url = embedding_service_url
        self.db_base = os.getenv("MIMICIV_DB_PATH")
        self.notes_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notes", "")
        self.ollama_client = ollama.Client(host=self.embedding_service_url)
        self.chroma_client = PersistentClient(path=self.chroma_base)
        self.admissions_collection_name = admissions_collection_name
        self.embeddings_created = embeddings_created
        self.trf_tokenizer = spacy.load("en_core_web_trf")
        

    def get_note_content(self, document_id: str) -> str:
        """
        Reads the content of a note file.

        Args:
            document_id (str): Path to the note file.

        Returns:
            str: Content of the note.
        """
        with open(document_id, "r") as note:
            return note.read()

    def get_embeddings(self, content: str):
        """
        Generates embeddings for the given content.

        Args:
            content (str): Text content to generate embeddings for.

        Returns:
            tuple: A tuple containing sentences and their corresponding embeddings.
        """
        content = content.replace("\\n", "\n")

        doc = self.trf_tokenizer(content)
        sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]

        embeddings = []
        for sentence in sentences:
            response = requests.post(self.embedding_service_url,
                headers={"Content-Type": "application/json"},
                json={"model": self.embedding_model, "prompt": sentence}
            ).json()

            embedding = response["embedding"]
            embeddings.append(embedding)

        return sentences, embeddings

    async def create_all_embeddings(self) -> bool:
        """
        Creates embeddings for all patient admission notes.

        Returns:
            bool: True if embeddings are successfully created, False otherwise.
        """
        if self.embeddings_created:
            return True

        try:
            subject_ids = []
            with PatientServices(self.db_base) as patients:
                subject_ids = patients.get_subject_ids()
            
            if not subject_ids:
                print("No subject IDs found.")
                return False
            
            try:
                self.chroma_client.delete_collection(self.admissions_collection_name)
            except Exception as e:
                print(f"Error deleting collection: {e}")
            adm_collection = self.chroma_client.create_collection(self.admissions_collection_name)

            with PatientServices(self.db_base) as patients:
                items = patients.get_subject_ids()
                for subject_id in [item["subject_id"] for item in items]:
                    note_content = await patients.get_notes(str(subject_id))
                    if not note_content:
                        print(f"No notes found for subject ID {subject_id}.")
                        continue
                    
                    note_content = f"<admission_note>{note_content}</admission_note>"
                    sentences, embeddings = self.get_embeddings(note_content)

                    for k, (sentence, embedding) in enumerate(zip(sentences, embeddings)):
                        unique_id = f"{subject_id}.{k}"
                        adm_collection.upsert(
                            ids=[unique_id],
                            embeddings=embedding,
                            documents=sentence,
                            metadatas=[{
                                "admission_data": str(subject_id),
                                "admission_note": note_content
                            }]
                        )
                        print(f"Added id {unique_id} to Vector Store")
                    print(f"Processed subject ID {subject_id} with {len(sentences)} sentences.")

            self.embeddings_created = True
            print(f"Embeddings created for {len(subject_ids)} subjects.")
        except Exception as e:
            print(e)
            return False

        return True

    def query_admissions_embeddings(self, query: str, result_set_size: int = 1):
        """
        Queries the embeddings for a given query string.

        Args:
            query (str): Query string.
            top_k (int): Number of top results to return.

        Returns:
            QueryResult: Results of the query.
        """
        adm_collection = self.chroma_client.get_or_create_collection(self.admissions_collection_name)
        print(f"Current collection size: {adm_collection.count()}")
        _, embedding = self.get_embeddings(query)
        results = adm_collection.query(query_embeddings=embedding, n_results=result_set_size)
        return results

    def query_admissions_patients(self, first_name: str, family_name: str, top_k: int) -> QueryResult:
        """
        Queries the embeddings for a specific patient.

        Args:
            first_name (str): Patient's first name.
            family_name (str): Patient's family name.
            top_k (int): Number of top results to return.

        Returns:
            QueryResult: Results of the query.
        """
        adm_collection = self.chroma_client.get_or_create_collection(self.admissions_collection_name)
        query = f"{first_name.lower()} {family_name.lower()}"
        _, embedding = self.get_embeddings(query)
        results = adm_collection.query(
            query_embeddings=embedding,
            n_results=top_k,
            where={"patient_name": query}
        )
        return results

if __name__ == "__main__":
    import asyncio

    embedding_url = os.environ.get("EMBEDDING_SERVICE_URL", 
                              "http://host.docker.internal:11440/api/embeddings")
    em = EmbeddingManager(embedding_service_url=embedding_url,
                          embeddings_created=False)
    
    asyncio.run(em.create_all_embeddings())
    

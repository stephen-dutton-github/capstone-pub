# Vector Service API - Clinical Diagnosis Pipeline — README

This project is a **neuro-symbolic clinical diagnosis system** that integrates **structured patient data**, **x-ray imaging**, and **Large Language Model (LLM)** reasoning to produce and evaluate diagnoses. The system supports **multi-modal workflows** and is extensible for research and clinical deployment.

---

## Project Overview

The core functionality revolves around a pipeline that:

1. Extracts patient information and admission records.
2. Generates synthetic clinical admission notes (if needed).
3. Uses a CNN to analyze x-ray images.
4. Combines structured and unstructured inputs to query an LLM.
5. Evaluates LLM and CNN predictions against ground-truth (ICD) labels.
6. Supports embedding generation and semantic search for patient similarity.

---

## Key Components

### 1. **DiagnosisGraph & DiagnosisManager**
- **File:** `diagnosis_graph.py`, `diagnosis_manager.py`
- **Purpose:** Defines the diagnosis workflow as a graph of asynchronous operations using `langgraph`. It handles tasks such as:
  - Data loading (notes, x-rays)
  - X-ray classification
  - Prompt building & anonymization
  - LLM interaction and function dispatching
  - Evaluation of model performance vs. ICD labels
- `DiagnosisManager` is the orchestration layer that manages graph execution for individual or batch patients.

### 2. **LLM Dispatcher**
- **File:** `llm_dispatcher.py`
- **Purpose:** Facilitates JSON-based function calling from LLM responses.
- Handles:
  - Parsing JSON responses embedded in LLM output
  - Dispatching the appropriate function with extracted arguments
  - Emitting events for debugging or streaming

### 3. **NotesManager**
- **File:** `notes_manager.py`
- **Purpose:** Creates hospital admission notes based on structured patient data using LLM prompts.
- Can auto-generate realistic medical histories for each patient to feed into the diagnosis workflow.

### 4. **EmbeddingManager**
- **File:** `embedding_manager.py`
- **Purpose:** Generates sentence-level embeddings for patient notes and stores them in a **ChromaDB** vector store.
- Supports:
  - Bulk embedding creation
  - Querying by text or patient name
  - Semantic search across patient records

### 5. **PatientServices**
- **File:** `patient_services.py`
- **Purpose:** Provides database interaction for:
  - Patient and admission lookup
  - Retrieving x-rays and clinical notes
  - Fetching ICD codes
- Implements a rich interface using `sqlite3` and Pydantic data models.

### 6. **DataManager**
- **File:** `data_manager.py`
- **Purpose:** Low-level SQLite manager used as a base for `PatientServices`.
- Provides safe read/write operations, error handling, and context management for SQL execution.

---

## Workflow Summary

1. **Initialize Services** using `DiagnosisManager`.
2. **Generate Notes** using `NotesManager.create_all_notes()` if needed.
3. **Run Diagnosis** via `get_diagnosis_report(...)`.
   - Optionally enable `multi_modal` for x-ray + note diagnosis.
4. **LLM Dispatch** is triggered from within the diagnosis graph.
5. **Results** include LLM and CNN diagnoses, confidence scores, and comparison with ICD labels.
6. **Embeddings** can be generated and queried to find similar patients.

---

## Environment Variables

Ensure the following environment variables are configured:

- `MIMICIV_DB_PATH`: Path to SQLite database.
- `OLLAMA_DEFAULT_MODEL`: Default LLM model name.
- `XRAY_PREDICTION_URL`: REST endpoint for CNN model inference.
- `LLM_SERVICE_URL`: REST endpoint for LLM function calling.
- `CHROMA_DB_PATH`: Path to Chroma vector database.

---

## Running the System

### Generate Notes
```bash
python notes_manager.py
```

### Run Full Diagnosis
```bash
python diagnosis_manager.py
```

### Generate Embeddings
```bash
python embedding_manager.py
```

---

## 📁 Directory Structure

```
.
├── data_manager.py
├── diagnosis_graph.py
├── diagnosis_manager.py
├── embedding_manager.py
├── llm_dispatcher.py
├── notes_manager.py
├── patient_services.py
└── notes/                # Auto-generated notes
```

---

## 🧪 Use Cases

- Evaluating diagnostic agreement between models and ICD labels.
- Exploring LLM reliability on clinical text.
- Multimodal reasoning with imaging + text.
- Semantic retrieval of similar patients.

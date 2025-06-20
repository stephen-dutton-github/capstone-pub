# Capstone, Stephed Dutton, CSCK700, 2025

## Clinical Diagnosis Docker Architecture

This repository defines a modular multi-service architecture for deploying a clinical diagnostic system powered by large language models (LLMs), x-ray image analysis, and vector-based semantic search.

## Overview

The system is composed using Docker Compose and includes the following major services:

- **ollama**: Local LLM inference engine with GPU acceleration.
- **open-webui**: Frontend interface for interacting with LLM services.
- **vector**: Embedding generation and vector database service.
- **xray**: Image-based diagnostic service using CNN models.

Each service is containerized, runs independently, and is GPU-enabled for accelerated performance.

---

## Services

### ollama

- **Purpose**: Hosts the LLM backend for prompt-based inference.
- **Build Context**: `./ollama`
- **Ports**: 
  - External: `${OLLAMA_BASE_PORT}`
  - Internal: `11434`
- **GPU**: Enabled (NVIDIA devices)
- **Volume**: Persistent model storage under `ollama:/root/.ollama`
- **Healthcheck**: Uses HTTP probe on `/` every 30s

### open-webui

- **Purpose**: Provides a web UI interface to interact with the `ollama` LLM backend.
- **Image**: `ghcr.io/open-webui/open-webui:main`
- **Depends On**: `ollama` (waits until healthy)
- **Environment**: Reads from `.env`, forwards `OLLAMA_BASE_URL`
- **Ports**:
  - External: `${OPEN_WEB_UI_BASE_PORT}`
  - Internal: `8080`
- **Volume**: Persists UI data under `open-webui:/app/backend/data`

### vector

- **Purpose**: Hosts the vector service for generating embeddings and supporting similarity search.
- **Build Context**: `./vector`
- **Depends On**: `ollama`
- **Ports**:
  - External: `${VECTOR_BASE_PORT}`
  - Internal: `8000`
- **Volume**: Mounted at `vector:/app`
- **GPU**: Enabled

### xray

- **Purpose**: Runs x-ray image analysis models for pulmonary diagnosis.
- **Build Context**: `./xray`
- **Ports**:
  - External: `${XRAY_BASE_PORT}`
  - Internal: `8000`
  - Additional: `5688` (for internal/debug use)
- **Volume**: Mounted at `xray:/app`
- **GPU**: Enabled

---

## Volumes

Each container has a bind-mounted volume for persistent storage and data exchange:

- `ollama`: Bound to `./ollama`
- `open-webui`: Bound to `./openWebUi/data`
- `vector`: Bound to `./vector`
- `xray`: Bound to `./xray`

These mappings allow data to persist across container rebuilds and ensure service-specific configurations are retained.

---

## Cleanup

Use the provided `docker-cleanup.sh` script to remove dangling Docker images, unused volumes, and stopped containers to maintain a clean environment.

---

## Environment Variables

The services rely on the following `.env` configuration variables:

- `OLLAMA_BASE_PORT`
- `OPEN_WEB_UI_BASE_PORT`
- `VECTOR_BASE_PORT`
- `XRAY_BASE_PORT`

Set these in a `.env` file at the root of your project before launching the stack.

---

## Launch

To start all services:

```bash
docker-compose up --build
```

To stop and remove all running containers:

```bash
docker-compose down
```

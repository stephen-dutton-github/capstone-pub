# Ollama Service — LLM Inference Engine

The `ollama` service is a dedicated Large Language Model (LLM) runtime component in the clinical diagnostic system. It handles all inference requests that require text generation or function-calling logic, making it a foundational layer for multi-modal diagnosis, LLM dispatching, and prompt-driven workflows.

## Role in the Architecture

The `ollama` container acts as the **backend LLM engine** and integrates with other services such as:

- **DiagnosisGraph / Dispatcher** (e.g., `llm_dispatcher.py`): Sends prompts and function call instructions to this service.
- **open-webui**: A frontend interface that proxies requests to the Ollama backend.
- **vector**: Embedding and semantic search services that may re-use the same LLM backend model.
- **notes_manager**: Uses the Ollama model to generate synthetic clinical notes.

It provides GPU-accelerated model inference and is optimized to cache models on disk for fast reuse.

---

## Functionality and Behavior

- Loads and serves LLMs (e.g., LLaMA, Mistral, or domain-specific medical models).
- Receives prompt input and returns generated text or structured function-call responses.
- Operates over HTTP on port `11434` by default.
- Uses a persistent volume (`ollama:/root/.ollama`) to cache models and reduce warm-up time.

---

## Model Caching

The directory `/root/.ollama` is mounted as a volume. This allows:

- Pre-loaded models to persist across container restarts.
- Reduced model download and initialization time.
- Faster warm-start when scaling or redeploying containers.

Example cached models might include:
- `llama3-med42-8b`
- `mistral-med`
- `gpt4all-llm`

---

## Docker Configuration Highlights

- **Build Context**: `./ollama`
- **GPU Support**: Uses NVIDIA runtime with `all` devices and `gpu` capability.
- **Healthcheck**: Periodically probes the service at `http://localhost:11434`
- **Environment Binding**: Exposes the port set in `OLLAMA_BASE_PORT`
- **Extra Hosts**: Includes `host.docker.internal` for inter-container requests

---

## API Usage

While Ollama exposes an HTTP-based API, direct use is abstracted behind:
- LLMDispatcher class in the main application
- FastAPI apps that call into Ollama with predefined prompt formats
- Web UI interface for human interaction (via `open-webui`)

Example request body from internal services:
```json
{
  "model": "thewindmom/llama3-med42-8b:latest",
  "prompt": "Summarize the following medical report...",
  "stream": false
}
```

---

## Integration

To use this service in other Python modules or workflows:
- Set the `OLLAMA_DEFAULT_MODEL` environment variable
- Use the `DispatcherClient` to send function-call formatted prompts
- Bind `OLLAMA_BASE_PORT` in `.env` for uniform access across services

---

## Launch and Monitoring

The container is launched with Docker Compose and restarts automatically. Health status can be checked via:

```bash
curl http://localhost:11434
```

This endpoint returns a 200 OK response when the model runtime is active and responsive.

---

## Persistent Volume

```yaml
volumes:
  ollama:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./ollama
```

This ensures that the model cache is retained between container builds and is essential for performance in production setups.

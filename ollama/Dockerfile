FROM ollama/ollama:latest


# Enable GPU support
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility
ENV OLLAMA_DEFAULT_MODEL=thewindmom/llama3-med42-8b

# Set working directory
WORKDIR /root/.ollama

RUN apt-get update && apt-get install -y curl


# Expose Ollama's API port
EXPOSE 11434

# Default command to run Ollama
ENTRYPOINT ["ollama","serve"]

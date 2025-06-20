# Base image with CUDA + cuDNN + Ubuntu
FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04

# Update and install Python, pip, git, and build tools
RUN apt-get update && apt-get install -y \
    python3-dev python3-pip git build-essential \
    libglib2.0-0 libsm6 libxext6 libxrender-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install TensorFlow
RUN pip install --upgrade pip && \
    pip install tensorflow==2.13.0 tensorflow-addons==0.20.0

WORKDIR /app

COPY . /app

RUN pip3 install --no-cache-dir -r /app/requirements.txt

# Expose app and debug ports
EXPOSE 10001 5688 8000

# Default entrypoint for debug and development (override with `docker run --entrypoint` if needed)
ENTRYPOINT ["python3", "-m", "debugpy", "--listen", "0.0.0.0:5688", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

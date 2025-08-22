# Multi-stage Dockerfile for 9P Social Analytics
FROM ubuntu:22.04 as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies with retry logic
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-distutils \
    python3-pip \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.11 /usr/bin/python \
    && ln -sf /usr/bin/python3.11 /usr/bin/python3

# Create app user
RUN groupadd -r app && useradd -r -g app app

# Set work directory
WORKDIR /app

# Copy requirements
COPY pyproject.toml ./
RUN pip install -e .

# Copy application code
COPY . .

# Change ownership to app user
RUN chown -R app:app /app
USER app

# FastAPI/Control service
FROM base as control
EXPOSE 8000
CMD ["uvicorn", "control.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Celery worker service
FROM base as worker
CMD ["celery", "-A", "worker.main", "worker", "--loglevel=info"]

# Celery beat scheduler
FROM base as scheduler
CMD ["celery", "-A", "worker.main", "beat", "--loglevel=info"]

# Streamlit web service
FROM base as web
EXPOSE 8501
CMD ["streamlit", "run", "web/main.py", "--server.port=8501", "--server.address=0.0.0.0"]

# vLLM inference service
FROM nvidia/cuda:11.8-devel-ubuntu20.04 as vllm-base

# Install Python 3.11
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-distutils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install pip
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# Set Python 3.11 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Install vLLM and dependencies
RUN pip install vllm==0.2.7 transformers torch

# Create app user
RUN groupadd -r app && useradd -r -g app app

WORKDIR /app

# Copy vLLM server script
COPY inference/vllm_server.py ./
RUN chown -R app:app /app
USER app

FROM vllm-base as vllm
EXPOSE 8080
CMD ["python", "vllm_server.py"]

# Use multi-stage build to reduce final image size (optional but recommended)
FROM public.ecr.aws/docker/library/python:3.11-slim AS builder
 
WORKDIR /app
 
# Install build dependencies only for this stage
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        portaudio19-dev \
        libportaudio2 \
        libportaudiocpp0 && \
    rm -rf /var/lib/apt/lists/*
 
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt
 
 
# Final runtime image
FROM public.ecr.aws/docker/library/python:3.11-slim
 
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
 
WORKDIR /app
 
# Runtime dependencies (minimal)
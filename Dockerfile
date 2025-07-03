FROM public.ecr.aws/docker/library/python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install build tools + PortAudio headers and libs
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      portaudio19-dev \
      libportaudio2 \
      libportaudiocpp0 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Upgrade pip, install pip-tools, compile a lockfile, then install from that
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --use-deprecated=legacy-resolver -r requirements.txt

# Copy the rest of your app
COPY . .

EXPOSE 3000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000", "--workers", "2"]

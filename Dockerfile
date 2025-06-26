FROM public.ecr.aws/docker/library/python:3.11-slim
 
# Set environment variables early
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
 
# Pre-install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      portaudio19-dev \
      libportaudio2 \
      libportaudiocpp0 \
      gcc \
&& rm -rf /var/lib/apt/lists/*
 
# Set working directory
WORKDIR /app
 
# Only copy requirements first for better layer caching
COPY requirements.txt .
 
# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
 
# Now copy the rest of the app
COPY . .
 
# Expose the app port
EXPOSE 3000
 
# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000", "--workers", "2"]
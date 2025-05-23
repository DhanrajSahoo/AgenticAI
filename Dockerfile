# Use Amazon ECR Public base image to avoid Docker Hub rate limits
FROM public.ecr.aws/docker/library/python:3.11-slim

# Environment variables to optimize Python behavior
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application code
COPY . .

# Expose the app port
EXPOSE 80

# Start the FastAPI app using Uvicorn
CMD ["uvicorn", "workflows.main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]

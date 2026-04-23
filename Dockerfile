FROM python:3.11-slim

LABEL maintainer="Champion Scholars Institute"
LABEL description="JEE/NEET English to Tamil AI Translator"

# Install system packages
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    poppler-utils \
    gcc \
    g++ \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Create data folders
RUN mkdir -p data/input_pdfs data/structured_json data/output_docx

# Download the translation model at build time (works offline later)
RUN python scripts/download_models.py

# Web UI port
EXPOSE 8000

# Start the web app
CMD ["uvicorn", "src.web_app:app", "--host", "0.0.0.0", "--port", "8000"]

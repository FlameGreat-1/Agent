# Base image with CUDA support
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

# Prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    cmake \
    python3 \
    python3-pip \
    python3-dev \
    ffmpeg \
    wget \
    curl \
    libsndfile1 \
    libblas-dev \
    liblapack-dev \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set up Python environment
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Create directories for models
RUN mkdir -p /app/models/whisper \
    /app/models/tts \
    /app/models/llm

# Install Whisper.cpp
RUN git clone https://github.com/ggerganov/whisper.cpp.git /app/whisper.cpp \
    && cd /app/whisper.cpp \
    && make \
    && bash ./models/download-ggml-model.sh large \
    && mv models/ggml-large.bin /app/models/whisper/

# Install Piper TTS
RUN git clone https://github.com/rhasspy/piper.git /app/piper \
    && cd /app/piper \
    && mkdir -p voices \
    && curl -L https://github.com/rhasspy/piper/releases/download/v1.2.0/voice-en-us-kathleen-high.tar.gz | tar -xz -C voices/ \
    && mv voices/en-us-kathleen-high.onnx /app/models/tts/

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Copy application code
COPY src/ /app/src/
COPY scripts/ /app/scripts/

# Make scripts executable
RUN chmod +x /app/scripts/*.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose API port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/app/scripts/entrypoint.sh"]

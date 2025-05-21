#!/bin/bash
# Create directories
export OLLAMA_MODELS=/workspace/ollama/models
mkdir -p /workspace/ollama/models
mkdir -p /workspace/temp-ai-agent

# Fix config to use workspace for temp files
if grep -q "/tmp/ai-agent" /workspace/Agent/app/config.py; then
    sed -i "s|TEMP_DIR = Path(\"/tmp/ai-agent\")|TEMP_DIR = Path(\"/workspace/temp-ai-agent\")|" /workspace/Agent/app/config.py
fi

# Start Ollama with GPU optimization
OLLAMA_MODELS=/workspace/ollama/models OLLAMA_GPU=1 OLLAMA_NUM_GPU_LAYERS=99 CUDA_VISIBLE_DEVICES=0 /usr/local/bin/ollama serve &
sleep 10

# Pull model if not already downloaded
if ! OLLAMA_MODELS=/workspace/ollama/models ollama list | grep -q "llama2"; then
    OLLAMA_MODELS=/workspace/ollama/models ollama pull llama2
fi

# Start API
cd /workspace/Agent && source venv/bin/activate && PYTHONPATH=/workspace/Agent uvicorn app.main:app --host 0.0.0.0 --port 8888 --workers 1

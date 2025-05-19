#!/bin/bash
export TMPDIR=/workspace/tmp
mkdir -p $TMPDIR
mkdir -p /workspace/ngrok
mkdir -p /workspace/ngrok_config

# Start Ollama with GPU
OLLAMA_MODELS=/workspace/ollama/models OLLAMA_GPU=1 ollama serve &
sleep 5

# Start your API
cd /workspace/Agent
PYTHONPATH=$PYTHONPATH:/workspace/Agent/app python app/src/main.py --host 0.0.0.0 &
sleep 5

# Start ngrok tunnel
source /workspace/venv/bin/activate
python /workspace/tunnel.py &

# Keep the container running
tail -f /dev/null

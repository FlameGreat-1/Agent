#!/bin/bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh
mkdir -p /workspace/{ollama/models,logs,temp-ai-agent}
# Update config
[ -f "/workspace/Agent/app/config.py" ] && sed -i "s|/tmp/ai-agent|/workspace/temp-ai-agent|; s|/app/models/|/workspace/Agent/app/models/|g; s|mixtral:8x7b-q4_K_M|agent-model:latest|" /workspace/Agent/app/config.py
# Setup supervisor
cat > /etc/supervisor/conf.d/ai-agent.conf << EOF
[program:ollama]
command=OLLAMA_MODELS=/workspace/ollama/models OLLAMA_GPU=1 OLLAMA_NUM_GPU_LAYERS=99 CUDA_VISIBLE_DEVICES=0 ollama serve
autostart=true
autorestart=true
stderr_logfile=/workspace/logs/ollama.err.log
stdout_logfile=/workspace/logs/ollama.out.log
[program:ai-agent]
command=cd /workspace/Agent && source venv/bin/activate && PYTHONPATH=/workspace/Agent uvicorn app.main:app --host 0.0.0.0 --port 8888 --workers 1
autostart=true
autorestart=true
stderr_logfile=/workspace/logs/ai-agent.err.log
stdout_logfile=/workspace/logs/ai-agent.out.log
[group:ai-services]
programs=ollama,ai-agent
EOF
echo "FROM llama2
PARAMETER num_gpu 99" > /workspace/Modelfile.llama
supervisord && sleep 10
ollama create agent-model -f /workspace/Modelfile.llama

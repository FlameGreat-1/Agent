# AI Agent Setup Documentation

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![GPU Accelerated](https://img.shields.io/badge/GPU-Accelerated-green.svg)](https://nvidia.com/cuda)

## 🎯 Overview

A comprehensive AI Agent system featuring speech-to-text (STT), text-to-speech (TTS), and large language model (LLM) capabilities with full GPU acceleration support. This system is optimized for production deployment with persistent storage and enterprise-grade process management.

## 🏗️ System Architecture

### Core Components
- **🎤 Whisper STT Model**: Large-v3 (2.88GB) - High-accuracy speech recognition
- **🔊 Piper TTS Model**: Lessac high-quality voice (113MB) - Natural speech synthesis  
- **🧠 Ollama LLM**: llama2 with GPU acceleration - Conversational AI
- **⚡ GPU Acceleration**: NVIDIA CUDA support for optimal performance
- **📊 Supervisor**: Production-ready process management

## 🚀 Quick Start

### Prerequisites
- Ubuntu/Debian-based system
- Python 3.8+
- NVIDIA GPU with CUDA support (recommended)
- 50GB+ available storage

### 1. Initial System Setup

```bash
# Update system packages
apt-get update 
apt-get install -y python3 python3-pip git python3-venv

# Clone the repository
cd /workspace 
git clone https://github.com/FlameGreat-1/Agent.git 
cd Agent 

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 📦 Model Configuration

### 🎤 Whisper STT Model Setup

```bash
# Create models directory
mkdir -p /workspace/Agent/app/models/whisper

# Download Whisper large-v3 model (2.88GB)
wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin \
  -O /workspace/Agent/app/models/whisper/ggml-large.bin

# Update configuration path
sed -i 's|WHISPER_MODEL_PATH: str = Field("/app/models/whisper/ggml-large.bin"|WHISPER_MODEL_PATH: str = Field("/workspace/Agent/app/models/whisper/ggml-large.bin"|' \
  /workspace/Agent/app/config.py
```

### 🔊 TTS Model Setup

```bash
# Create TTS models directory
mkdir -p /workspace/Agent/app/models/tts

# Download Amy voice model (60MB)
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx \
  -O /workspace/Agent/app/models/tts/en-us-kathleen-high.onnx

# Update configuration path
sed -i 's|TTS_MODEL_PATH: str = Field("/app/models/tts/en-us-kathleen-high.onnx"|TTS_MODEL_PATH: str = Field("/workspace/Agent/app/models/tts/en-us-kathleen-high.onnx"|' \
  /workspace/Agent/app/config.py
```

### 🧠 LLM Setup with Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Create models directory
mkdir -p /workspace/ollama/models

# Configure environment and start Ollama
OLLAMA_MODELS=/workspace/ollama/models ollama serve &

# Wait for initialization
until curl -s http://localhost:11434/api/tags >/dev/null 2>&1; do
    echo "Waiting for Ollama API..."
    sleep 2
done

# Pull llama2 model (3.8GB)
ollama pull llama2

# Create GPU-optimized model configuration
cat > /workspace/Modelfile.llama << EOF
FROM llama2
PARAMETER num_gpu 1
EOF

# Create optimized agent model
ollama create agent-model -f /workspace/Modelfile.llama

# Update configuration
sed -i 's|OLLAMA_MODEL: str = Field("mixtral:8x7b-q4_K_M"|OLLAMA_MODEL: str = Field("agent-model:latest"|' \
  /workspace/Agent/app/config.py
```

## ⚡ GPU Acceleration Configuration

### System Requirements
- NVIDIA GPU (tested with NVIDIA A40)
- CUDA drivers installed
- Container with GPU access

### Setup GPU Acceleration

```bash
# Configure Ollama with GPU support
export CUDA_VISIBLE_DEVICES=0
export OLLAMA_MODELS=/workspace/ollama/models
export OLLAMA_GPU=1
export OLLAMA_NUM_GPU_LAYERS=33

# Kill existing processes
pkill -9 ollama
sleep 2

# Start Ollama with GPU settings
ollama serve > /workspace/ollama.log 2>&1 &
sleep 10

# Create GPU-optimized model
cat > /workspace/Modelfile.llama << 'EOF'
FROM llama2
PARAMETER num_gpu 33
EOF

ollama create agent-model -f /workspace/Modelfile.llama

# Install PyTorch with CUDA support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Verify GPU detection
python3 -c "import torch; print('CUDA available:', torch.cuda.is_available())"
```

## 🔧 Production Deployment

### Supervisor Configuration

```bash
# Install Supervisor
apt update && apt install -y supervisor
mkdir -p /workspace/logs

# Create configuration
cat > /etc/supervisor/conf.d/ai-agent.conf << 'EOF'
[program:ollama]
command=/bin/bash -c "OLLAMA_MODELS=/workspace/ollama/models OLLAMA_GPU=1 OLLAMA_NUM_GPU_LAYERS=99 CUDA_VISIBLE_DEVICES=0 ollama serve"
autostart=true
autorestart=true
stderr_logfile=/workspace/logs/ollama.err.log
stdout_logfile=/workspace/logs/ollama.out.log

[program:ai-agent]
command=/bin/bash -c "cd /workspace/Agent && source venv/bin/activate && PYTHONPATH=/workspace/Agent uvicorn app.main:app --host 0.0.0.0 --port 8888 --workers 1"
autostart=true
autorestart=true
stderr_logfile=/workspace/logs/ai-agent.err.log
stdout_logfile=/workspace/logs/ai-agent.out.log

[group:ai-services]
programs=ollama,ai-agent
EOF

# Start services
supervisorctl reread
supervisorctl update
supervisorctl start ai-services:*
```

### Persistent Startup Script

```bash
# Create comprehensive startup script
cat > /workspace/startup.sh << 'EOF'
#!/bin/bash

# Kill existing processes
pkill -9 ollama
pkill -9 python

# Set temporary directory in workspace
export TMPDIR=/workspace/tmp
mkdir -p $TMPDIR

# Configure GPU acceleration
export CUDA_VISIBLE_DEVICES=0
export OLLAMA_MODELS=/workspace/ollama/models
export OLLAMA_GPU=1
export OLLAMA_NUM_GPU_LAYERS=33
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128
export TRANSFORMERS_CACHE=/workspace/.cache/huggingface
export HF_HOME=/workspace/.cache/huggingface

# Start Ollama with GPU support
ollama serve > /workspace/ollama.log 2>&1 &
sleep 10

# Verify Ollama startup
if curl -s http://localhost:11434/api/tags > /dev/null; then
  echo "✅ Ollama started successfully"
else
  echo "❌ Failed to start Ollama"
  cat /workspace/ollama.log
  exit 1
fi

# Create GPU-optimized model
cat > /workspace/Modelfile.llama << 'MODEL'
FROM llama2
PARAMETER num_gpu 33
MODEL

ollama create agent-model -f /workspace/Modelfile.llama

# Start API server
cd /workspace/Agent
source venv/bin/activate
PYTHONPATH=/workspace/Agent uvicorn app.main:app --host 0.0.0.0 --port 8888 --workers 1
EOF

chmod +x /workspace/startup.sh

# Add to automatic startup
echo "/workspace/startup.sh" >> /root/.bashrc
```

## 🔄 Running the Application

### Manual Start
```bash
cd /workspace/Agent
source venv/bin/activate
PYTHONPATH=$PYTHONPATH:/workspace/Agent python app/src/main.py
```

### Production Start
```bash
# Start all services
supervisorctl start ai-services:*

# Check status
supervisorctl status
```

## 🧪 API Testing

### Health Check
```bash
curl http://localhost:8888/health
```

### Speech-to-Text (Transcription)
```bash
# Using base64 audio
curl -X POST http://localhost:8888/transcribe \
  -H "Content-Type: application/json" \
  -d '{"audio_base64":"BASE64_AUDIO_HERE","language":"en"}'

# Using file upload
curl -X POST http://localhost:8888/transcribe \
  -F "file=@/path/to/audio.wav" \
  -F "language=en"
```

### Text Generation (LLM)
```bash
curl -X POST http://localhost:8888/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is artificial intelligence?",
    "system_prompt": "You are a helpful AI assistant.",
    "temperature": 0.7,
    "max_tokens": 500
  }'
```

### Text-to-Speech (TTS)
```bash
# Get base64 audio response
curl -X POST http://localhost:8888/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test of the text to speech system.",
    "speaker": "default",
    "output_format": "wav"
  }'

# Stream audio directly
curl -X POST http://localhost:8888/synthesize/stream \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test of the text to speech system.",
    "speaker": "default",
    "output_format": "wav"
  }' --output speech.wav
```

### Complete Pipeline (STT-LLM-TTS)
```bash
# Text input with audio response
curl -X POST http://localhost:8888/process \
  -H "Content-Type: application/json" \
  -d '{
    "text": "What is the capital of France?",
    "system_prompt": "You are a helpful AI assistant.",
    "temperature": 0.7,
    "return_audio": true
  }'

# Audio input with audio response
curl -X POST http://localhost:8888/process \
  -H "Content-Type: application/json" \
  -d '{
    "audio_base64": "BASE64_AUDIO_HERE",
    "language": "en",
    "system_prompt": "You are a helpful AI assistant.",
    "temperature": 0.7,
    "return_audio": true
  }'
```

## 📊 Performance Metrics

### Before GPU Acceleration
- **CPU Usage**: 100% utilization
- **GPU Usage**: 3% memory, 0% compute
- **Response Time**: Timeouts (>180 seconds)
- **Token Generation**: 1.45 tokens/second

### After GPU Acceleration
- **Response Time**: ~4.68 seconds for 500 tokens
- **Token Generation**: 104.92 tokens/second (72x faster)
- **GPU Usage**: Active utilization during inference
- **Power Usage**: 21W → 60-66W during processing
- **Temperature**: 26°C → 30-31°C during processing

### Model Specifications
| Component | Model | Size | Purpose |
|-----------|-------|------|---------|
| **STT** | Whisper Large-v3 | 2.88GB | Speech-to-text conversion |
| **TTS** | Piper Amy Voice | 60MB | Text-to-speech synthesis |
| **LLM** | Llama2 (Ollama) | 3.8GB | Natural language processing |

## 🔍 Monitoring & Troubleshooting

### GPU Monitoring
```bash
# Real-time GPU monitoring
nvidia-smi -l 1

# Check GPU availability in Python
python3 -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('GPU device count:', torch.cuda.device_count())"
```

### Service Status
```bash
# Check all services
supervisorctl status

# View logs
tail -f /workspace/logs/ollama.out.log
tail -f /workspace/logs/ai-agent.out.log
```

### Common Issues

#### Disk Space Issues
```bash
# Set temporary directory to workspace
export TMPDIR=/workspace/tmp
mkdir -p $TMPDIR
```

#### Ollama Not Using GPU
```bash
# Check Ollama log
cat /workspace/ollama.log

# Verify GPU visibility
nvidia-smi

# Restart with explicit GPU settings
export OLLAMA_GPU=1
export CUDA_VISIBLE_DEVICES=0
ollama serve
```

#### Timeout Issues
```bash
# Increase timeout in configuration
sed -i 's/timeout=180/timeout=600/g' /workspace/Agent/app/core/llm.py
```

## 🔐 Security Configuration

### API Key Authentication
If API key authentication is enabled, add the header to all requests:
```bash
-H "X-API-Key: your-api-key-here"
```

### Environment Variables
```bash
# Required for GPU acceleration
export CUDA_VISIBLE_DEVICES=0
export OLLAMA_GPU=1
export OLLAMA_MODELS=/workspace/ollama/models

# Optional optimizations
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128
export TRANSFORMERS_CACHE=/workspace/.cache/huggingface
export HF_HOME=/workspace/.cache/huggingface
```

## 📁 Directory Structure

```
/workspace/
├── Agent/                     # Main application
│   ├── app/
│   │   ├── models/
│   │   │   ├── whisper/      # STT models
│   │   │   └── tts/          # TTS models
│   │   ├── src/              # Source code
│   │   └── config.py         # Configuration
│   ├── venv/                 # Virtual environment
│   └── requirements.txt
├── ollama/
│   └── models/               # LLM models
├── logs/                     # Service logs
├── .cache/                   # Model cache
└── startup.sh                # Startup script
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the logs in `/workspace/logs/`

---

**Note**: This system is optimized for NVIDIA GPUs and requires significant computational resources. For production deployment, ensure adequate hardware specifications and monitor resource usage regularly.
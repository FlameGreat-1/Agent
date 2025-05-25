
### 1. Health Check

curl http://localhost:8888/api/health

### 2. Text Generation (LLM)

curl -X POST http://localhost:8888/api/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: 7f8e9d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8" \
  -d '{
    "prompt": "What is artificial intelligence?",
    "system_prompt": "You are a helpful AI assistant.",
    "temperature": 0.7,
    "max_tokens": 500,
    "stream": false
  }'


### 3. Text-to-Speech (TTS)

curl -X POST http://localhost:8888/api/synthesize \
  -H "Content-Type: application/json" \
  -H "X-API-Key: 7f8e9d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8" \
  -d '{
    "text": "Hello, this is a test of the text to speech system.",
    "speaker": "default",
    "output_format": "wav"
  }'


### 4. Text-to-Speech Streaming

curl -X POST http://localhost:8888/api/synthesize/stream \
  -H "Content-Type: application/json" \
  -H "X-API-Key: 7f8e9d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8" \
  -d '{
    "text": "Hello, this is a test of the text to speech system.",
    "speaker": "default",
    "output_format": "wav"
  }' --output speech.wav


### 5. Complete Process (Text Input → LLM → TTS)

curl -X POST http://localhost:8888/api/process \
  -H "Content-Type: application/json" \
  -H "X-API-Key: 7f8e9d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8" \
  -d '{
    "text": "What is the capital of France?",
    "system_prompt": "You are a helpful AI assistant.",
    "temperature": 0.7,
    "return_audio": true
  }'


For frontend integration, use these updated URLs:

https://alhgtq3p5oelru-8888.proxy.runpod.net/api/health
https://alhgtq3p5oelru-8888.proxy.runpod.net/api/generate
https://alhgtq3p5oelru-8888.proxy.runpod.net/api/synthesize
https://alhgtq3p5oelru-8888.proxy.runpod.net/api/synthesize/stream
https://alhgtq3p5oelru-8888.proxy.runpod.net/api/process


Remember to include the API key in all requests:

-H "X-API-Key: 7f8e9d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8"


Let's test the endpoints using the proxy URL from outside the web terminal:

1. **Health Check**:

curl https://alhgtq3p5oelru-8888.proxy.runpod.net/api/health


2. **Text Generation (non-streaming)**:

curl -X POST https://alhgtq3p5oelru-8888.proxy.runpod.net/api/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: 7f8e9d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8" \
  -d '{
    "prompt": "What is artificial intelligence?",
    "system_prompt": "You are a helpful AI assistant.",
    "temperature": 0.7,
    "max_tokens": 200,
    "stream": false
  }'


3. **Text Generation (streaming)**:

curl -X POST https://alhgtq3p5oelru-8888.proxy.runpod.net/api/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: 7f8e9d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8" \
  -d '{
    "prompt": "Write a short poem about AI",
    "system_prompt": "You are a helpful AI assistant.",
    "temperature": 0.7,
    "max_tokens": 200,
    "stream": true
  }'


4. **Text-to-Speech**:

curl -X POST https://alhgtq3p5oelru-8888.proxy.runpod.net/api/synthesize \
  -H "Content-Type: application/json" \
  -H "X-API-Key: 7f8e9d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8" \
  -d '{
    "text": "Hello, this is a test of the text to speech system.",
    "speaker": "default",
    "output_format": "wav"
  }'


5. **Complete Process (Text → LLM → TTS)**:

curl -X POST https://alhgtq3p5oelru-8888.proxy.runpod.net/api/process \
  -H "Content-Type: application/json" \
  -H "X-API-Key: 7f8e9d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8" \
  -d '{
    "text": "What is the capital of France?",
    "system_prompt": "You are a helpful AI assistant.",
    "temperature": 0.7,
    "return_audio": true
  }'


These commands can be run from any machine with internet access. The proxy URL makes your API accessible from anywhere, not just from within the pod.



NOTE THIS ENDPOINT FORMAT FOR WINDOWS CLI:              

curl -X POST https://alhgtq3p5oelru-8888.proxy.runpod.net/api/generate -H "Content-Type: application/json" -H "X-API-Key: 7f8e9d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8" -d "{\"prompt\":\"What is artificial intelligence?\",\"system_prompt\":\"You are a helpful AI assistant.\",\"temperature\":0.7,\"max_tokens\":200,\"stream\":false}"


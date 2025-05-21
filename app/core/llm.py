import json
import logging
import requests
import uuid
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator

from app.config import settings
from app.utils.logging import log_execution_time

logger = logging.getLogger(__name__)

class LanguageModelService:
    def __init__(self, 
                 host: str = settings.OLLAMA_HOST, 
                 port: int = settings.OLLAMA_PORT,
                 model: str = settings.OLLAMA_MODEL):
        self.base_url = f"http://{host}:{port}/api"
        self.model = model
        self._validate_connection()
        logger.info(f"Initialized LLM service with model: {self.model}")
    
    def _validate_connection(self) -> None:
        try:
            response = requests.get(f"{self.base_url}/tags")
            response.raise_for_status()
            models = response.json().get("models", [])
            model_names = [m.get("name") for m in models]
            
            if not models or self.model not in model_names:
                logger.warning(f"Model {self.model} not found in Ollama. Available models: {model_names}")
        except requests.RequestException as e:
            error_msg = f"Failed to connect to Ollama API: {str(e)}"
            logger.error(error_msg)
            raise ConnectionError(error_msg)
    
    @log_execution_time
    def generate(self, 
                prompt: str, 
                system_prompt: Optional[str] = None,
                temperature: float = 0.7,
                max_tokens: int = 1024,
                conversation_history: Optional[List[Dict[str, str]]] = None,
                image_base64: Optional[str] = None,
                image_url: Optional[str] = None,
                stream: bool = False) -> Dict[str, Any]:
        job_id = str(uuid.uuid4())
        logger.info(f"Starting LLM generation job {job_id}")
        
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": stream,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
                
            if conversation_history:
                messages = []
                for msg in conversation_history:
                    if msg.get("role") and msg.get("content"):
                        messages.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })
                if messages:
                    payload["messages"] = messages
            
            if image_base64:
                payload["image_data"] = image_base64
                
            if image_url:
                payload["image_url"] = image_url
            
            logger.debug(f"Sending request to Ollama: {json.dumps(payload)}")
            
            if stream:
                return self._handle_streaming(payload, job_id)
            else:
                response = requests.post(
                    f"{self.base_url}/generate",
                    json=payload,
                    timeout=60
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"Completed LLM generation job {job_id}")
                
                return {
                    "job_id": job_id,
                    "text": result.get("response", ""),
                    "model": self.model,
                    "success": True,
                    "metadata": {
                        "eval_count": result.get("eval_count"),
                        "eval_duration": result.get("eval_duration")
                    },
                    "usage": {
                        "prompt_tokens": result.get("prompt_eval_count", 0),
                        "completion_tokens": result.get("eval_count", 0),
                        "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
                    },
                    "finish_reason": "stop"
                }
                
        except requests.RequestException as e:
            logger.exception(f"Error in LLM generation job {job_id}: {str(e)}")
            return {
                "job_id": job_id,
                "error": str(e),
                "success": False
            }
    
    def _handle_streaming(self, payload: Dict[str, Any], job_id: str) -> Dict[str, Any]:
        try:
            with requests.post(
                f"{self.base_url}/generate",
                json=payload,
                stream=True,
                timeout=120
            ) as response:
                response.raise_for_status()
                
                full_text = ""
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        text_chunk = chunk.get("response", "")
                        full_text += text_chunk
                        
                        yield {
                            "text": text_chunk,
                            "finish_reason": None
                        }
                
                yield {
                    "text": "",
                    "finish_reason": "stop"
                }
                
                logger.info(f"Completed streaming LLM generation job {job_id}")
                
                return {
                    "job_id": job_id,
                    "text": full_text,
                    "model": self.model,
                    "success": True
                }
                
        except requests.RequestException as e:
            logger.exception(f"Error in streaming LLM generation job {job_id}: {str(e)}")
            return {
                "job_id": job_id,
                "error": str(e),
                "success": False
            }
    
    async def generate_async(self,
                           prompt: str, 
                           system_prompt: Optional[str] = None,
                           temperature: float = 0.7,
                           max_tokens: int = 1024,
                           conversation_history: Optional[List[Dict[str, str]]] = None,
                           image_base64: Optional[str] = None,
                           image_url: Optional[str] = None,
                           stream: bool = False) -> AsyncGenerator[Dict[str, Any], None]:
        job_id = str(uuid.uuid4())
        logger.info(f"Starting async LLM generation job {job_id}")
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
            
        if conversation_history:
            messages = []
            for msg in conversation_history:
                if msg.get("role") and msg.get("content"):
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            if messages:
                payload["messages"] = messages
        
        if image_base64:
            payload["image_data"] = image_base64
            
        if image_url:
            payload["image_url"] = image_url
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/generate",
                    json=payload,
                    timeout=120
                ) as response:
                    response.raise_for_status()
                    
                    full_text = ""
                    async for line in response.content:
                        if line:
                            try:
                                chunk = json.loads(line)
                                text_chunk = chunk.get("response", "")
                                full_text += text_chunk
                                
                                yield {
                                    "text": text_chunk,
                                    "finish_reason": None
                                }
                            except json.JSONDecodeError:
                                continue
                    
                    yield {
                        "text": "",
                        "finish_reason": "stop"
                    }
                    
                    logger.info(f"Completed async streaming LLM generation job {job_id}")
        except Exception as e:
            logger.exception(f"Error in async streaming LLM generation job {job_id}: {str(e)}")
            yield {
                "text": "",
                "error": str(e),
                "finish_reason": "error"
            }

"""
Language Model service using Ollama.
Follows Single Responsibility Principle by focusing only on text processing.
"""
import json
import logging
import requests
import uuid
from typing import Dict, Any, List, Optional

from app.config import settings
from app.utils.logging import log_execution_time

logger = logging.getLogger(__name__)

class LanguageModelService:
    """Enterprise-grade language model service using Ollama."""
    
    def __init__(self, 
                 host: str = settings.OLLAMA_HOST, 
                 port: int = settings.OLLAMA_PORT,
                 model: str = settings.OLLAMA_MODEL):
        """
        Initialize the LLM service with connection and model settings.
        
        Args:
            host: Ollama API host
            port: Ollama API port
            model: Model name to use
        """
        self.base_url = f"http://{host}:{port}/api"
        self.model = model
        self._validate_connection()
        logger.info(f"Initialized LLM service with model: {self.model}")
    
    def _validate_connection(self) -> None:
        """Validate connection to Ollama API."""
        try:
            response = requests.get(f"{self.base_url}/tags")
            response.raise_for_status()
            # Check if our model is available
            models = response.json().get("models", [])
            model_names = [m.get("name") for m in models]
            
            if not models or self.model not in model_names:
                logger.warning(f"Model {self.model} not found in Ollama. Available models: {model_names}")
                # We don't raise an error here as the model might be pulled later
        except requests.RequestException as e:
            error_msg = f"Failed to connect to Ollama API: {str(e)}"
            logger.error(error_msg)
            raise ConnectionError(error_msg)
    
    @log_execution_time
    def generate(self, 
                prompt: str, 
                system_prompt: Optional[str] = None,
                temperature: float = 0.7,
                max_tokens: int = 1024) -> Dict[str, Any]:
        """
        Generate text response from the language model.
        
        Args:
            prompt: User input text
            system_prompt: Optional system instructions
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dict containing generated text and metadata
            
        Raises:
            RuntimeError: If generation fails
        """
        # Create a unique ID for this generation job
        job_id = str(uuid.uuid4())
        logger.info(f"Starting LLM generation job {job_id}")
        
        try:
            # Prepare request payload
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            # Add system prompt if provided
            if system_prompt:
                payload["system"] = system_prompt
            
            # Send request to Ollama
            logger.debug(f"Sending request to Ollama: {json.dumps(payload)}")
            response = requests.post(
                f"{self.base_url}/generate",
                json=payload,
                timeout=60  # Reasonable timeout for generation
            )
            
            # Check for errors
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
                }
            }
            
        except requests.RequestException as e:
            logger.exception(f"Error in LLM generation job {job_id}: {str(e)}")
            return {
                "job_id": job_id,
                "error": str(e),
                "success": False
            }

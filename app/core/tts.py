"""
Text-to-Speech service using Piper.
Follows Single Responsibility Principle by focusing only on speech synthesis.
"""
import os
import uuid
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, BinaryIO

from app.config import settings
from app.utils.logging import log_execution_time

logger = logging.getLogger(__name__)

class TextToSpeechService:
    """Enterprise-grade text-to-speech service using Piper."""
    
    def __init__(self, model_path: str = settings.TTS_MODEL_PATH,
                 num_threads: int = settings.TTS_THREADS):
        """
        Initialize the TTS service with model path and performance settings.
        
        Args:
            model_path: Path to the Piper model file
            num_threads: Number of threads to use for processing
        """
        self.model_path = model_path
        self.num_threads = num_threads
        self._validate_model()
        logger.info(f"Initialized TTS service with model: {self.model_path}")
    
    def _validate_model(self) -> None:
        """Validate that the model file exists."""
        if not os.path.exists(self.model_path):
            error_msg = f"TTS model not found at {self.model_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
    
    @log_execution_time
    def synthesize(self, 
                  text: str, 
                  speaker: Optional[str] = None,
                  output_format: str = "wav") -> Dict[str, Any]:
        """
        Synthesize text to speech.
        
        Args:
            text: Text to synthesize
            speaker: Optional speaker voice
            output_format: Output audio format (wav, mp3)
            
        Returns:
            Dict containing audio data and metadata
            
        Raises:
            RuntimeError: If synthesis fails
        """
        # Create a unique ID for this synthesis job
        job_id = str(uuid.uuid4())
        logger.info(f"Starting TTS synthesis job {job_id}")
        
        try:
            # Create temporary output file
            with tempfile.NamedTemporaryFile(suffix=f'.{output_format}', delete=False) as temp_file:
                output_path = temp_file.name
            
            # Build command for Piper
            cmd = [
                f"{settings.BASE_DIR}/piper/piper",
                "--model", self.model_path,
                "--output_file", output_path,
                "--json-input", "false",
                "--output-raw", "false"
            ]
            
            # Add speaker if specified
            if speaker:
                cmd.extend(["--speaker", speaker])
            
            # Execute Piper
            logger.debug(f"Executing command: {' '.join(cmd)}")
            process = subprocess.run(
                cmd,
                input=text.encode('utf-8'),
                capture_output=True,
                check=False  # We'll handle errors manually
            )
            
            # Check for errors
            if process.returncode != 0:
                error_msg = f"TTS synthesis failed: {process.stderr.decode('utf-8')}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            # Read the output audio file
            with open(output_path, 'rb') as f:
                audio_data = f.read()
            
            logger.info(f"Completed TTS synthesis job {job_id}")
            
            return {
                "job_id": job_id,
                "audio_data": audio_data,
                "format": output_format,
                "success": True,
                "text_length": len(text)
            }
            
        except Exception as e:
            logger.exception(f"Error in TTS synthesis job {job_id}: {str(e)}")
            return {
                "job_id": job_id,
                "error": str(e),
                "success": False
            }
        finally:
            # Clean up temporary file
            if 'output_path' in locals() and os.path.exists(output_path):
                os.unlink(output_path)

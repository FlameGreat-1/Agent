"""
Speech-to-Text service using Whisper.cpp.
Follows Single Responsibility Principle by focusing only on speech recognition.
"""
import os
import uuid
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, BinaryIO

from app.config import settings
from app.utils.logging import log_execution_time

logger = logging.getLogger(__name__)

class SpeechToTextService:
    """Enterprise-grade speech-to-text service using Whisper.cpp."""
    
    def __init__(self, model_path: str = settings.WHISPER_MODEL_PATH, 
                 num_threads: int = settings.WHISPER_THREADS):
        """
        Initialize the STT service with model path and performance settings.
        
        Args:
            model_path: Path to the Whisper model file
            num_threads: Number of threads to use for processing
        """
        self.model_path = model_path
        self.num_threads = num_threads
        self._validate_model()
        logger.info(f"Initialized STT service with model: {self.model_path}")
    
    def _validate_model(self) -> None:
        """Validate that the model file exists."""
        if not os.path.exists(self.model_path):
            error_msg = f"Whisper model not found at {self.model_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
    
    @log_execution_time
    def transcribe(self, audio_data: BinaryIO, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Transcribe audio data to text.
        
        Args:
            audio_data: Binary audio data
            language: Optional language code (e.g., 'en', 'fr')
            
        Returns:
            Dict containing transcription results and metadata
        
        Raises:
            RuntimeError: If transcription fails
        """
        # Create a unique ID for this transcription job
        job_id = str(uuid.uuid4())
        logger.info(f"Starting transcription job {job_id}")
        
        try:
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
                # Write audio data to temp file
                audio_data.seek(0)
                temp_file.write(audio_data.read())
            
            # Build command for Whisper.cpp
            cmd = [
                f"{settings.BASE_DIR}/whisper.cpp/main",
                "-m", self.model_path,
                "-f", temp_path,
                "-t", str(self.num_threads),
                "--output-txt"
            ]
            
            # Add language parameter if specified
            if language:
                cmd.extend(["-l", language])
            
            # Execute Whisper.cpp
            logger.debug(f"Executing command: {' '.join(cmd)}")
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False  # We'll handle errors manually
            )
            
            # Check for errors
            if process.returncode != 0:
                error_msg = f"Whisper transcription failed: {process.stderr}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            # Parse output
            transcription = process.stdout.strip()
            
            # Also read the output text file if it exists
            txt_path = f"{temp_path}.txt"
            if os.path.exists(txt_path):
                with open(txt_path, 'r') as f:
                    transcription = f.read().strip()
                # Clean up text file
                os.unlink(txt_path)
            
            logger.info(f"Completed transcription job {job_id}")
            
            return {
                "job_id": job_id,
                "text": transcription,
                "language": language or "auto",
                "success": True
            }
            
        except Exception as e:
            logger.exception(f"Error in transcription job {job_id}: {str(e)}")
            return {
                "job_id": job_id,
                "error": str(e),
                "success": False
            }
        finally:
            # Clean up temporary file
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.unlink(temp_path)

"""
API request and response schemas.
Follows Interface Segregation Principle by defining clear, specific interfaces.
"""
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, validator
import base64

class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")

class ErrorResponse(BaseModel):
    """Standard error response schema."""
    detail: str = Field(..., description="Error details")
    code: Optional[str] = Field(None, description="Error code")
    trace_id: Optional[str] = Field(None, description="Trace ID for debugging")

# Speech-to-Text schemas
class TranscriptionRequest(BaseModel):
    """Request schema for speech-to-text transcription."""
    language: Optional[str] = Field(None, description="Language code (e.g., 'en', 'fr')")
    audio_base64: Optional[str] = Field(None, description="Base64-encoded audio data")
    
    @validator('audio_base64')
    def validate_audio(cls, v):
        """Validate audio data is properly encoded."""
        if v is None:
            return v
        try:
            base64.b64decode(v)
            return v
        except Exception:
            raise ValueError("Invalid base64 encoding for audio data")

class TranscriptionResponse(BaseModel):
    """Response schema for speech-to-text transcription."""
    job_id: str = Field(..., description="Unique job identifier")
    text: str = Field(..., description="Transcribed text")
    language: str = Field(..., description="Language used for transcription")
    success: bool = Field(..., description="Whether transcription was successful")
    error: Optional[str] = Field(None, description="Error message if unsuccessful")

# Language Model schemas
class GenerationRequest(BaseModel):
    """Request schema for language model text generation."""
    prompt: str = Field(..., description="User input text")
    system_prompt: Optional[str] = Field(None, description="System instructions")
    temperature: float = Field(0.7, description="Sampling temperature (0.0 to 1.0)")
    max_tokens: int = Field(1024, description="Maximum tokens to generate")

class GenerationResponse(BaseModel):
    """Response schema for language model text generation."""
    job_id: str = Field(..., description="Unique job identifier")
    text: str = Field(..., description="Generated text")
    model: str = Field(..., description="Model used for generation")
    success: bool = Field(..., description="Whether generation was successful")
    error: Optional[str] = Field(None, description="Error message if unsuccessful")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

# Text-to-Speech schemas
class SynthesisRequest(BaseModel):
    """Request schema for text-to-speech synthesis."""
    text: str = Field(..., description="Text to synthesize")
    speaker: Optional[str] = Field(None, description="Speaker voice")
    output_format: str = Field("wav", description="Output audio format")

class SynthesisResponse(BaseModel):
    """Response schema for text-to-speech synthesis."""
    job_id: str = Field(..., description="Unique job identifier")
    audio_base64: Optional[str] = Field(None, description="Base64-encoded audio data")
    format: str = Field(..., description="Audio format")
    success: bool = Field(..., description="Whether synthesis was successful")
    error: Optional[str] = Field(None, description="Error message if unsuccessful")

# Complete pipeline schemas
class ProcessRequest(BaseModel):
    """Request schema for complete STT-LLM-TTS pipeline."""
    audio_base64: Optional[str] = Field(None, description="Base64-encoded audio data")
    text: Optional[str] = Field(None, description="Text input (alternative to audio)")
    system_prompt: Optional[str] = Field(None, description="System instructions for LLM")
    return_audio: bool = Field(True, description="Whether to return audio response")
    language: Optional[str] = Field(None, description="Language code for STT")
    temperature: float = Field(0.7, description="Sampling temperature for LLM")
    
    @validator('audio_base64', 'text')
    def validate_input(cls, v, values):
        """Validate that either audio or text is provided."""
        if 'audio_base64' not in values and 'text' not in values:
            raise ValueError("Either audio_base64 or text must be provided")
        return v

class ProcessResponse(BaseModel):
    """Response schema for complete STT-LLM-TTS pipeline."""
    job_id: str = Field(..., description="Unique job identifier")
    input_text: Optional[str] = Field(None, description="Transcribed input text")
    output_text: str = Field(..., description="Generated output text")
    audio_base64: Optional[str] = Field(None, description="Base64-encoded output audio")
    format: Optional[str] = Field(None, description="Audio format if audio returned")
    success: bool = Field(..., description="Whether processing was successful")
    error: Optional[str] = Field(None, description="Error message if unsuccessful")

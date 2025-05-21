from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, validator
import base64

class HealthResponse(BaseModel):
    status: str = Field(...)
    version: str = Field(...)

class ErrorResponse(BaseModel):
    detail: str = Field(...)
    code: Optional[str] = Field(None)
    trace_id: Optional[str] = Field(None)

class TranscriptionRequest(BaseModel):
    language: Optional[str] = Field(None)
    audio_base64: Optional[str] = Field(None)
    
    @validator('audio_base64')
    def validate_audio(cls, v):
        if v is None:
            return v
        try:
            base64.b64decode(v)
            return v
        except Exception:
            raise ValueError("Invalid base64 encoding for audio data")

class TranscriptionResponse(BaseModel):
    job_id: str = Field(...)
    text: str = Field(...)
    language: str = Field(...)
    success: bool = Field(...)
    error: Optional[str] = Field(None)

class GenerationRequest(BaseModel):
    prompt: str = Field(...)
    system_prompt: Optional[str] = Field(None)
    temperature: float = Field(0.7)
    max_tokens: int = Field(1024)
    conversation_history: Optional[List[Dict[str, str]]] = Field(None)
    image_base64: Optional[str] = Field(None)
    image_url: Optional[str] = Field(None)
    stream: Optional[bool] = Field(False)
    
    @validator('image_base64')
    def validate_image(cls, v):
        if v is None:
            return v
        try:
            base64.b64decode(v)
            return v
        except Exception:
            raise ValueError("Invalid base64 encoding for image data")

class GenerationResponse(BaseModel):
    job_id: str = Field(...)
    text: str = Field(...)
    model: str = Field(...)
    success: bool = Field(...)
    error: Optional[str] = Field(None)
    metadata: Optional[Dict[str, Any]] = Field(None)
    usage: Optional[Dict[str, int]] = Field(None)
    finish_reason: Optional[str] = Field(None)

class StreamChunk(BaseModel):
    text: str = Field(...)
    finish_reason: Optional[str] = Field(None)

class SynthesisRequest(BaseModel):
    text: str = Field(...)
    speaker: Optional[str] = Field(None)
    output_format: str = Field("wav")

class SynthesisResponse(BaseModel):
    job_id: str = Field(...)
    audio_base64: Optional[str] = Field(None)
    format: str = Field(...)
    success: bool = Field(...)
    error: Optional[str] = Field(None)

class ProcessRequest(BaseModel):
    audio_base64: Optional[str] = Field(None)
    text: Optional[str] = Field(None)
    system_prompt: Optional[str] = Field(None)
    return_audio: bool = Field(True)
    language: Optional[str] = Field(None)
    temperature: float = Field(0.7)
    image_base64: Optional[str] = Field(None)
    image_url: Optional[str] = Field(None)
    
    @validator('audio_base64', 'text')
    def validate_input(cls, v, values):
        if 'audio_base64' not in values and 'text' not in values:
            raise ValueError("Either audio_base64 or text must be provided")
        return v
    
    @validator('image_base64')
    def validate_image(cls, v):
        if v is None:
            return v
        try:
            base64.b64decode(v)
            return v
        except Exception:
            raise ValueError("Invalid base64 encoding for image data")

class ProcessResponse(BaseModel):
    job_id: str = Field(...)
    input_text: Optional[str] = Field(None)
    output_text: str = Field(...)
    audio_base64: Optional[str] = Field(None)
    format: Optional[str] = Field(None)
    success: bool = Field(...)
    error: Optional[str] = Field(None)

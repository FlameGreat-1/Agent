"""
API router implementation.
Follows Dependency Inversion Principle by depending on abstractions.
"""
import logging
import base64
import io
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Header
from fastapi.responses import StreamingResponse

from app.src.api.schemas import (
    TranscriptionRequest, TranscriptionResponse,
    GenerationRequest, GenerationResponse,
    SynthesisRequest, SynthesisResponse,
    ProcessRequest, ProcessResponse,
    ErrorResponse
)
from app.src.core.stt import SpeechToTextService
from app.src.core.llm import LanguageModelService
from app.src.core.tts import TextToSpeechService
from app.src.config import settings
from app.src.utils.monitoring import STT_LATENCY, LLM_LATENCY, TTS_LATENCY

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["ai"])

# Create service instances
stt_service = SpeechToTextService()
llm_service = LanguageModelService()
tts_service = TextToSpeechService()

# API key validation dependency
async def validate_api_key(x_api_key: Optional[str] = Header(None)):
    """
    Validate API key if enabled.
    
    Args:
        x_api_key: API key from request header
        
    Raises:
        HTTPException: If API key is invalid
    """
    if settings.API_KEY_ENABLED:
        if not x_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key is required"
            )
        if x_api_key != settings.API_KEY:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )

# Speech-to-Text endpoint
@router.post("/transcribe", response_model=TranscriptionResponse, responses={
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
    500: {"model": ErrorResponse}
})
async def transcribe(
    request: TranscriptionRequest = None,
    file: Optional[UploadFile] = File(None),
    language: Optional[str] = Form(None),
    _: None = Depends(validate_api_key)
):
    """
    Transcribe speech to text.
    
    Args:
        request: Transcription request with base64 audio
        file: Audio file upload (alternative to base64)
        language: Language code (overrides request.language)
        
    Returns:
        Transcription response with text
    """
    # Validate input
    if not request and not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either request body or file upload is required"
        )
    
    try:
        # Process audio from file upload or base64
        if file:
            audio_data = io.BytesIO(await file.read())
            lang = language
        else:
            if not request.audio_base64:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="audio_base64 is required in request body"
                )
            # Decode base64 audio
            audio_bytes = base64.b64decode(request.audio_base64)
            audio_data = io.BytesIO(audio_bytes)
            lang = language or request.language
        
        # Measure STT performance
        with STT_LATENCY.labels(success="true").time():
            # Transcribe audio
            result = stt_service.transcribe(audio_data, lang)
        
        if not result["success"]:
            # Record failure in metrics
            STT_LATENCY.labels(success="false").observe(0)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Transcription failed")
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in transcribe endpoint")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Language Model endpoint
@router.post("/generate", response_model=GenerationResponse, responses={
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
    500: {"model": ErrorResponse}
})
async def generate(
    request: GenerationRequest,
    _: None = Depends(validate_api_key)
):
    """
    Generate text using language model.
    
    Args:
        request: Generation request with prompt
        
    Returns:
        Generation response with text
    """
    try:
        # Measure LLM performance
        with LLM_LATENCY.labels(success="true", model=settings.OLLAMA_MODEL).time():
            # Generate text
            result = llm_service.generate(
                prompt=request.prompt,
                system_prompt=request.system_prompt,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
        
        if not result["success"]:
            # Record failure in metrics
            LLM_LATENCY.labels(success="false", model=settings.OLLAMA_MODEL).observe(0)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Text generation failed")
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in generate endpoint")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Text-to-Speech endpoint
@router.post("/synthesize", response_model=SynthesisResponse, responses={
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
    500: {"model": ErrorResponse}
})
async def synthesize(
    request: SynthesisRequest,
    _: None = Depends(validate_api_key)
):
    """
    Synthesize text to speech.
    
    Args:
        request: Synthesis request with text
        
    Returns:
        Synthesis response with audio
    """
    try:
        # Measure TTS performance
        with TTS_LATENCY.labels(success="true").time():
            # Synthesize speech
            result = tts_service.synthesize(
                text=request.text,
                speaker=request.speaker,
                output_format=request.output_format
            )
        
        if not result["success"]:
            # Record failure in metrics
            TTS_LATENCY.labels(success="false").observe(0)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Speech synthesis failed")
            )
        
        # Encode audio data as base64
        audio_base64 = base64.b64encode(result["audio_data"]).decode("utf-8")
        
        return {
            **result,
            "audio_base64": audio_base64
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in synthesize endpoint")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Audio streaming endpoint
@router.post("/synthesize/stream", responses={
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
    500: {"model": ErrorResponse}
})
async def synthesize_stream(
    request: SynthesisRequest,
    _: None = Depends(validate_api_key)
):
    """
    Synthesize text to speech and return streaming audio response.
    
    Args:
        request: Synthesis request with text
        
    Returns:
        Streaming audio response
    """
    try:
        # Measure TTS performance
        with TTS_LATENCY.labels(success="true").time():
            # Synthesize speech
            result = tts_service.synthesize(
                text=request.text,
                speaker=request.speaker,
                output_format=request.output_format
            )
        
        if not result["success"]:
            # Record failure in metrics
            TTS_LATENCY.labels(success="false").observe(0)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Speech synthesis failed")
            )
        
        # Set content type based on format
        content_type = "audio/wav" if request.output_format == "wav" else "audio/mpeg"
        
        # Return streaming response
        return StreamingResponse(
            io.BytesIO(result["audio_data"]),
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename=speech.{request.output_format}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in synthesize_stream endpoint")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Complete pipeline endpoint
@router.post("/process", response_model=ProcessResponse, responses={
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
    500: {"model": ErrorResponse}
})
async def process(
    request: ProcessRequest,
    _: None = Depends(validate_api_key)
):
    """
    Process input through the complete STT-LLM-TTS pipeline.
    
    Args:
        request: Process request with audio or text input
        
    Returns:
        Process response with text and optional audio
    """
    try:
        input_text = None
        job_id = None
        
        # Step 1: Speech-to-Text (if audio provided)
        if request.audio_base64:
            audio_bytes = base64.b64decode(request.audio_base64)
            audio_data = io.BytesIO(audio_bytes)
            
            # Measure STT performance
            with STT_LATENCY.labels(success="true").time():
                stt_result = stt_service.transcribe(audio_data, request.language)
            
            if not stt_result["success"]:
                STT_LATENCY.labels(success="false").observe(0)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=stt_result.get("error", "Transcription failed")
                )
            
            input_text = stt_result["text"]
            job_id = stt_result["job_id"]
        else:
            # Use provided text input
            input_text = request.text
        
        # Step 2: Language Model
        with LLM_LATENCY.labels(success="true", model=settings.OLLAMA_MODEL).time():
            llm_result = llm_service.generate(
                prompt=input_text,
                system_prompt=request.system_prompt,
                temperature=request.temperature
            )
        
        if not llm_result["success"]:
            LLM_LATENCY.labels(success="false", model=settings.OLLAMA_MODEL).observe(0)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=llm_result.get("error", "Text generation failed")
            )
        
        output_text = llm_result["text"]
        job_id = job_id or llm_result["job_id"]
        
        # Step 3: Text-to-Speech (if requested)
        audio_base64 = None
        audio_format = None
        
        if request.return_audio:
            with TTS_LATENCY.labels(success="true").time():
                tts_result = tts_service.synthesize(
                    text=output_text,
                    output_format="wav"  # Default format
                )
            
            if not tts_result["success"]:
                TTS_LATENCY.labels(success="false").observe(0)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=tts_result.get("error", "Speech synthesis failed")
                )
            
            # Encode audio data as base64
            audio_base64 = base64.b64encode(tts_result["audio_data"]).decode("utf-8")
            audio_format = tts_result["format"]
        
        # Return complete response
        return {
            "job_id": job_id,
            "input_text": input_text,
            "output_text": output_text,
            "audio_base64": audio_base64,
            "format": audio_format,
            "success": True
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in process endpoint")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

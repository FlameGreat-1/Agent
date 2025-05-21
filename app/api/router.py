import logging
import base64
import io
import json
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Header
from fastapi.responses import StreamingResponse, Response

from app.api.schemas import (
    TranscriptionRequest, TranscriptionResponse,
    GenerationRequest, GenerationResponse, StreamChunk,
    SynthesisRequest, SynthesisResponse,
    ProcessRequest, ProcessResponse,
    ErrorResponse
)
from app.core.stt import SpeechToTextService
from app.core.llm import LanguageModelService
from app.core.tts import TextToSpeechService
from app.config import settings
from app.utils.monitoring import STT_LATENCY, LLM_LATENCY, TTS_LATENCY

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ai"])

stt_service = SpeechToTextService()
llm_service = LanguageModelService()
tts_service = TextToSpeechService()

async def validate_api_key(x_api_key: Optional[str] = Header(None)):
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
    if not request and not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either request body or file upload is required"
        )
    
    try:
        if file:
            audio_data = io.BytesIO(await file.read())
            lang = language
        else:
            if not request.audio_base64:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="audio_base64 is required in request body"
                )
            audio_bytes = base64.b64decode(request.audio_base64)
            audio_data = io.BytesIO(audio_bytes)
            lang = language or request.language
        
        with STT_LATENCY.labels(success="true").time():
            result = stt_service.transcribe(audio_data, lang)
        
        if not result["success"]:
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

@router.post("/generate", responses={
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
    500: {"model": ErrorResponse}
})
async def generate(
    request: GenerationRequest,
    _: None = Depends(validate_api_key)
):
    try:
        if request.stream:
            async def stream_generator():
                async for chunk in llm_service.generate_async(
                    prompt=request.prompt,
                    system_prompt=request.system_prompt,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    conversation_history=request.conversation_history,
                    image_base64=request.image_base64,
                    image_url=request.image_url,
                    stream=True
                ):
                    yield f"data: {json.dumps(chunk)}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                stream_generator(),
                media_type="text/event-stream"
            )
        
        with LLM_LATENCY.labels(success="true", model=settings.OLLAMA_MODEL).time():
            result = llm_service.generate(
                prompt=request.prompt,
                system_prompt=request.system_prompt,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                conversation_history=request.conversation_history,
                image_base64=request.image_base64,
                image_url=request.image_url
            )
        
        if not result["success"]:
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

@router.post("/synthesize", response_model=SynthesisResponse, responses={
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
    500: {"model": ErrorResponse}
})
async def synthesize(
    request: SynthesisRequest,
    _: None = Depends(validate_api_key)
):
    try:
        with TTS_LATENCY.labels(success="true").time():
            result = tts_service.synthesize(
                text=request.text,
                speaker=request.speaker,
                output_format=request.output_format
            )
        
        if not result["success"]:
            TTS_LATENCY.labels(success="false").observe(0)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Speech synthesis failed")
            )
        
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

@router.post("/synthesize/stream", responses={
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
    500: {"model": ErrorResponse}
})
async def synthesize_stream(
    request: SynthesisRequest,
    _: None = Depends(validate_api_key)
):
    try:
        with TTS_LATENCY.labels(success="true").time():
            result = tts_service.synthesize(
                text=request.text,
                speaker=request.speaker,
                output_format=request.output_format
            )
        
        if not result["success"]:
            TTS_LATENCY.labels(success="false").observe(0)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Speech synthesis failed")
            )
        
        content_type = "audio/wav" if request.output_format == "wav" else "audio/mpeg"
        
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

@router.post("/process", response_model=ProcessResponse, responses={
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
    500: {"model": ErrorResponse}
})
async def process(
    request: ProcessRequest,
    _: None = Depends(validate_api_key)
):
    try:
        input_text = None
        job_id = None
        
        if request.audio_base64:
            audio_bytes = base64.b64decode(request.audio_base64)
            audio_data = io.BytesIO(audio_bytes)
            
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
            input_text = request.text
        
        with LLM_LATENCY.labels(success="true", model=settings.OLLAMA_MODEL).time():
            llm_result = llm_service.generate(
                prompt=input_text,
                system_prompt=request.system_prompt,
                temperature=request.temperature,
                image_base64=request.image_base64,
                image_url=request.image_url
            )
        
        if not llm_result["success"]:
            LLM_LATENCY.labels(success="false", model=settings.OLLAMA_MODEL).observe(0)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=llm_result.get("error", "Text generation failed")
            )
        
        output_text = llm_result["text"]
        job_id = job_id or llm_result["job_id"]
        
        audio_base64 = None
        audio_format = None
        
        if request.return_audio:
            with TTS_LATENCY.labels(success="true").time():
                tts_result = tts_service.synthesize(
                    text=output_text,
                    output_format="wav"
                )
            
            if not tts_result["success"]:
                TTS_LATENCY.labels(success="false").observe(0)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=tts_result.get("error", "Speech synthesis failed")
                )
            
            audio_base64 = base64.b64encode(tts_result["audio_data"]).decode("utf-8")
            audio_format = tts_result["format"]
        
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

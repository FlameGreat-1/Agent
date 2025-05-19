"""
Monitoring utilities for the application.
"""
import time
from typing import Callable
from fastapi import FastAPI, Request, Response
from prometheus_client import Counter, Histogram, start_http_server
import logging

from src.config import settings

# Metrics
REQUEST_COUNT = Counter(
    'app_request_count',
    'Application Request Count',
    ['app_name', 'method', 'endpoint', 'status_code']
)

REQUEST_LATENCY = Histogram(
    'app_request_latency_seconds',
    'Application Request Latency',
    ['app_name', 'method', 'endpoint']
)

STT_LATENCY = Histogram(
    'stt_processing_seconds',
    'Speech-to-Text Processing Time',
    ['success']
)

LLM_LATENCY = Histogram(
    'llm_processing_seconds',
    'Language Model Processing Time',
    ['success', 'model']
)

TTS_LATENCY = Histogram(
    'tts_processing_seconds',
    'Text-to-Speech Processing Time',
    ['success']
)

logger = logging.getLogger(__name__)

def setup_metrics(app: FastAPI):
    """
    Setup Prometheus metrics collection for the application.
    
    Args:
        app: FastAPI application
    """
    # Start metrics server
    try:
        start_http_server(settings.METRICS_PORT)
        logger.info(f"Started metrics server on port {settings.METRICS_PORT}")
    except Exception as e:
        logger.error(f"Failed to start metrics server: {str(e)}")
    
    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Default status code if something goes wrong in the request handler
        status_code = 500
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            # Record request latency
            latency = time.time() - start_time
            endpoint = request.url.path
            
            REQUEST_LATENCY.labels(
                app_name='ai_agent',
                method=request.method,
                endpoint=endpoint
            ).observe(latency)
            
            # Record request count
            REQUEST_COUNT.labels(
                app_name='ai_agent',
                method=request.method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()

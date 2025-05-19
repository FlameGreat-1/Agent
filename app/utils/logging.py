"""
Logging utilities for the application.
"""
import logging
import time
import json
import functools
from typing import Callable, Any
import uuid
from datetime import datetime

from app.config import settings

def setup_logging():
    """Configure application-wide logging."""
    # Create formatter
    formatter = logging.Formatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", '
        '"message": "%(message)s", "trace_id": "%(trace_id)s"}'
    )
    
    # Add trace_id to log record
    old_factory = logging.getLogRecordFactory()
    
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.trace_id = getattr(record, 'trace_id', str(uuid.uuid4()))
        return record
    
    logging.setLogRecordFactory(record_factory)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Set specific log levels for noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

def log_execution_time(func: Callable) -> Callable:
    """
    Decorator to log function execution time.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start_time = time.time()
        
        # Generate trace ID for this operation
        trace_id = str(uuid.uuid4())
        
        logger.info(
            f"Starting {func.__name__}",
            extra={"trace_id": trace_id}
        )
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            logger.info(
                f"Completed {func.__name__} in {execution_time:.2f}s",
                extra={"trace_id": trace_id, "execution_time": execution_time}
            )
            
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            
            logger.error(
                f"Failed {func.__name__} after {execution_time:.2f}s: {str(e)}",
                extra={"trace_id": trace_id, "execution_time": execution_time},
                exc_info=True
            )
            
            raise
    
    return wrapper

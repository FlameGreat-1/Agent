import os
import sys

# Add the app directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

# Import the app from main.py
from src.main import app

if __name__ == "__main__":
    import uvicorn
    from src.config import settings
    
    print(f"Starting AI Agent API on {settings.API_HOST}:{settings.API_PORT}")
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        workers=settings.API_WORKERS,
    )

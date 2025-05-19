from pyngrok import ngrok, conf
import time
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set custom paths for ngrok
os.environ["NGROK_PATH"] = "/workspace/ngrok"
conf.get_default().ngrok_path = "/workspace/ngrok/ngrok"
conf.get_default().config_path = "/workspace/ngrok_config/config.yml"

# Add your auth token here
conf.get_default().auth_token = "2xJwE2DasBNvYa5qGIiGDYHXVS3_4M7V2S1sk8ZV3uG6usM8y"
conf.get_default().region = "us"

# Start the tunnel
http_tunnel = ngrok.connect(8000, "http")
public_url = http_tunnel.public_url
logger.info(f"ngrok tunnel established at: {public_url}")
logger.info("Use this URL in your Render backend configuration")

# Keep the script running
try:
    while True:
        time.sleep(60)
        logger.info(f"Tunnel still active at: {public_url}")
except KeyboardInterrupt:
    logger.info("Shutting down ngrok tunnel...")
    ngrok.disconnect(public_url)
    ngrok.kill()

"""
Script to run the Daphne ASGI server for WebSocket support
"""
import os
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    """Run the Daphne server"""
    logger.info("Starting Daphne server...")
    
    # Set the Django settings module path
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.config.settings')
    
    # Run Daphne with the ASGI application
    cmd = ["daphne", "-v", "2", "app.config.asgi:application"]
    
    logger.info(f"Running command: {' '.join(cmd)}")
    
    try:
        # Execute daphne and pass through all output
        process = subprocess.run(cmd, check=True)
        return process.returncode
    except subprocess.CalledProcessError as e:
        logger.error(f"Daphne failed with return code {e.returncode}")
        return e.returncode
    except KeyboardInterrupt:
        logger.info("Shutting down Daphne...")
        return 0

if __name__ == "__main__":
    main()

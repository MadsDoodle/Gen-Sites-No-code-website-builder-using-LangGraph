import uvicorn
import logging
from agent.api import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent_execution.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("="*60)
    logger.info("STARTING AI WEBSITE BUILDER API SERVER")
    logger.info("="*60)
    logger.info("Server will be available at: http://localhost:8000")
    logger.info("API documentation at: http://localhost:8000/docs")
    logger.info("="*60)
    
    uvicorn.run(
        "agent.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
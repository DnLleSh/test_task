import asyncio
import logging
import signal
import sys
from typing import Any

from app.services.rabbitmq import rabbitmq_service
from app.utils.logging import setup_logging
from app.worker.processor import ImageProcessor


setup_logging()
logger = logging.getLogger(__name__)


worker_running = True
processor = ImageProcessor()


async def message_handler(message: Any) -> None:
    try:
        await processor.process_message(message)
    except Exception as e:
        logger.error(f"Error in message handler: {e}")


async def start_worker() -> None:
    logger.info("Starting image processing worker")
    
    try:
        await rabbitmq_service.connect()
        logger.info("Connected to RabbitMQ")
        
        await rabbitmq_service.consume_messages(message_handler)
        logger.info("Started consuming messages")
        
        while worker_running:
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"Worker error: {e}")
        raise
    finally:
        await rabbitmq_service.disconnect()
        logger.info("Worker stopped")


def signal_handler(signum: int, frame: Any) -> None:
    global worker_running
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    worker_running = False


async def main() -> None:
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await start_worker()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Worker failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

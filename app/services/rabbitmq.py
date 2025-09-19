import json
import logging
from typing import Any, Dict

import aio_pika
from aio_pika import Connection, Exchange, Message, Queue
from aio_pika.abc import AbstractIncomingMessage

from app.config import settings

logger = logging.getLogger(__name__)


class RabbitMQService:
    def __init__(self) -> None:
        self.connection: Connection | None = None
        self.channel: aio_pika.Channel | None = None
        self.exchange: Exchange | None = None
        self.queue: Queue | None = None

    async def connect(self) -> None:
        try:
            self.connection = await aio_pika.connect_robust(settings.rabbitmq_url)
            self.channel = await self.connection.channel()
            
            self.exchange = await self.channel.declare_exchange(
                "image_processing", aio_pika.ExchangeType.DIRECT
            )
            
            self.queue = await self.channel.declare_queue(
                "images", durable=True
            )
            
            await self.queue.bind(self.exchange, "image_processing")
            
            logger.info("Connected to RabbitMQ successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def disconnect(self) -> None:
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("Disconnected from RabbitMQ")

    async def publish_message(self, routing_key: str, message: Dict[str, Any]) -> None:
        if not self.channel or not self.exchange:
            raise RuntimeError("RabbitMQ not connected")
            
        try:
            message_body = json.dumps(message).encode()
            await self.exchange.publish(
                Message(message_body, delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
                routing_key=routing_key
            )
            logger.info(f"Published message to queue: {routing_key}")
            
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise

    async def consume_messages(self, callback) -> None:
        if not self.queue:
            raise RuntimeError("RabbitMQ queue not initialized")
            
        try:
            await self.queue.consume(callback)
            logger.info("Started consuming messages from queue")
            
        except Exception as e:
            logger.error(f"Failed to start consuming messages: {e}")
            raise

    async def ack_message(self, message: AbstractIncomingMessage) -> None:
        try:
            message.ack()
            logger.debug("Message acknowledged")
        except Exception as e:
            logger.error(f"Failed to acknowledge message: {e}")

    async def nack_message(self, message: AbstractIncomingMessage, requeue: bool = True) -> None:
        try:
            message.nack(requeue=requeue)
            logger.debug(f"Message nacked, requeue: {requeue}")
        except Exception as e:
            logger.error(f"Failed to nack message: {e}")


rabbitmq_service = RabbitMQService()

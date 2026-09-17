import aio_pika
import json
from app.core.config import config

class RabbitMqManager:
    def __init__(self):
        self.connection: aio_pika.abc.AbstractRobustConnection | None=None
        self.channel: aio_pika.abc.AbstractRobustChannel | None=None

    async def connect(self):
        self.connection = await aio_pika.connect_robust(
            config.RABBITMQ_URL
        )

        self.channel = await self.connection.channel()

        await self.channel.declare_queue(
            "email_verification",
            durable=True,
        )

    async def publish(self, message:dict):
        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(message).encode()
            ),
            routing_key="email_verification"
        )
        
    async def close(self):
        if self.connection:
            self.connection.close()
rabbitmq_manager=RabbitMqManager()


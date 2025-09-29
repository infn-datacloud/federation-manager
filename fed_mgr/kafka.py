from typing import Callable
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import aiokafka as ak
import asyncio
import json

from fed_mgr.config import get_settings
from fed_mgr.logger import get_logger


class KafkaHandler:
    def __init__(self):
        self._settings = get_settings()
        self._consumer_context = self.__create_consumer_context()
        self._producer_context = self.__create_producer_context()
        self._logger = get_logger(self._settings, "kafka")

    def __create_consumer_context(self):
        context = {
            "client_id": self._settings.KAFKA_CLIENT_NAME,
            "bootstrap_servers": self._settings.KAFKA_BOOTSTRAP_SERVERS,
            "value_deserializer": lambda x: json.loads(x.decode("utf-8")),
            "fetch_max_bytes": self._settings.KAFKA_MAX_REQUEST_SIZE,
            "consumer_timeout_ms": self._settings.KAFKA_TIMEOUT,
            "auto_offset_reset": "earliest",
            "enable_auto_commit": False,
            "group_id": "fed-mgr-group",
            "max_poll_records": 1,
        }
        if self._settings.KAFKA_SSL_CERT_PATH is not None:
            ssl_context = self.__create_ssl_context()
            context = {**context, **ssl_context}
        return context

    def __create_producer_context(self):
        context = {
            "client_id": self._settings.KAFKA_CLIENT_NAME,
            "bootstrap_servers": self._settings.KAFKA_BOOTSTRAP_SERVERS,
            "value_serializer": lambda x: json.dumps(x, sort_keys=True).encode("utf-8"),
            "max_request_size": self._settings.KAFKA_MAX_REQUEST_SIZE,
            "acks": "all",
            "enable_idempotence": True,
        }
        if self._settings.KAFKA_SSL_CERT_PATH is not None:
            ssl_context = self.__create_ssl_context()
            context = {**context, **ssl_context}
        return context

    def __create_ssl_context(self) -> dict[str, str | dict[str, str | None]]:
        """Create AIOKafka SSL context

        Returns:
          dict[str, str]: AIOKafka SSL context
        """
        return {
            "security_protocol": "SSL",
            "ssl_context": {
                "ssl_cafile": self._settings.KAFKA_SSL_CERT_PATH,
                "ssl_certfile": self._settings.KAFKA_SSL_CERT_PATH,
                "ssl_keyfile": self._settings.KAFKA_SSL_KEY_PATH,
                "ssl_password": self._settings.KAFKA_SSL_PASSWORD
            }
        }

    def settings(self):
        return self._settings

    def listen_topic(self, *topic, callback: Callable[[ak.ConsumerRecord], None]) -> None:
        """Register an AIOKafkaConsumer"""
        asyncio.create_task(self._start_consumer(*topic, callback=callback))

    async def _start_consumer(self, *topic, callback: Callable[[ak.ConsumerRecord], None]) -> None:
        consumer = AIOKafkaConsumer(*topic, **self._consumer_context)
        await consumer.start()
        try:
            async for message in consumer:
                callback(message)
                await consumer.commit()
        finally:
            self._logger.info("Stopping KafkaConsumer")
            await consumer.stop()

    async def send_one(self, topic: str, message: bytes):
        producer = AIOKafkaProducer(bootstrap_servers=self._producer_context["bootstrap_servers"])
        # Get cluster layout and initial topic/partition leadership information
        await producer.start()
        try:
            # Produce message
            await producer.send_and_wait(topic, message)
            self._logger.debug("all messages dispatched")
        finally:
            # Wait for all pending messages to be delivered or expire.
            await producer.stop()

    def logger(self):
        return self._logger


class KafkaApp:
    def __init__(self):
        self._handler = KafkaHandler()
        self.__start()

    def __del__(self):
        self._handler.logger().info("KafkaApp exited")

    def __start(self):
        settings = self._handler.settings()
        self._handler.listen_topic(settings.KAFKA_EVALUATE_PROVIDERS_TOPIC, callback=self.on_message)
        self._handler.logger().info("KafkaApp started")

    def send(self, topic: str, message: bytes):
        asyncio.create_task(self._handler.send_one(topic, message))

    def on_message(self, message: ak.ConsumerRecord) -> None:
        self._handler.logger().debug(f"message arrived on topic {message.topic}, value: {message.value}")


async def main():
    app = KafkaApp()
    while True:
        app.send("evaluate-providers", b'{"msg": "hello!"}')
        await asyncio.sleep(2)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass

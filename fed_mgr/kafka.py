from typing import Callable, Set
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import aiokafka as ak
import asyncio
import json

from fed_mgr.config import get_settings
from fed_mgr.logger import get_logger


class KafkaHandler:
    def __init__(self):
        self._settings = get_settings()
        ssl_context = self.__create_ssl_context()
        self._consumer_context = self.__create_consumer_context(ssl_context)
        self._producer_context = self.__create_producer_context(ssl_context)
        self._logger = get_logger(self._settings, "kafka")
        self._tasks: Set[asyncio.Task] = set()

    def __del__(self):
        for task in self._tasks:
            if not task.done():
                task.cancel()

    def __create_consumer_context(self, ssl_context):
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
        if ssl_context:
            context = {**context, **ssl_context}
        return context

    def __create_producer_context(self, ssl_context):
        context = {
            "client_id": self._settings.KAFKA_CLIENT_NAME,
            "bootstrap_servers": self._settings.KAFKA_BOOTSTRAP_SERVERS,
            "value_serializer": lambda x: json.dumps(x, sort_keys=True).encode("utf-8"),
            "max_request_size": self._settings.KAFKA_MAX_REQUEST_SIZE,
            "acks": "all",
            "enable_idempotence": True,
        }
        if ssl_context:
            context = {**context, **ssl_context}
        return context

    def __create_ssl_context(self) -> dict[str, str | dict[str, str | None]] | None:
        if self._settings.KAFKA_SSL_CERT_PATH is None:
            return
        return {
            "security_protocol": "SSL",
            "ssl_context": {
                "ssl_cafile": self._settings.KAFKA_SSL_CERT_PATH,
                "ssl_certfile": self._settings.KAFKA_SSL_CERT_PATH,
                "ssl_keyfile": self._settings.KAFKA_SSL_KEY_PATH,
                "ssl_password": self._settings.KAFKA_SSL_PASSWORD
            }
        }

    async def __start_consumer(self, *topic, callback: Callable[[ak.ConsumerRecord], None]) -> None:
        consumer = AIOKafkaConsumer(*topic, **self._consumer_context)
        await consumer.start()
        try:
            async for message in consumer:
                callback(message)
                await consumer.commit()
        finally:
            self._logger.info("Stopping KafkaConsumer")
            await consumer.stop()

    async def __send_one(self, topic: str, message: str):
        producer = AIOKafkaProducer(**self._producer_context)
        await producer.start()
        try:
            await producer.send_and_wait(topic, message)
            self._logger.debug("all messages dispatched")
        finally:
            await producer.stop()

    def __on_task_complete(self, task):
        self._tasks.remove(task)

    def settings(self):
        return self._settings

    def logger(self):
        return self._logger

    def listen_topic(self, *topic, callback: Callable[[ak.ConsumerRecord], None]) -> None:
        task = asyncio.create_task(self.__start_consumer(*topic, callback=callback))
        task.add_done_callback(self.__on_task_complete)
        self._tasks.add(task)

    def send(self, topic: str, message: str):
        task = asyncio.create_task(self.__send_one(topic, message))
        task.add_done_callback(self.__on_task_complete)
        self._tasks.add(task)


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

    def send(self, topic: str, message: str):
        self._handler.send(topic, message)

    def on_message(self, message: ak.ConsumerRecord) -> None:
        self._handler.logger().debug(f"message arrived on topic {message.topic}, value: {message.value}")


async def main():
    app = KafkaApp()
    while True:
        app.send("evaluate-providers", '{"msg": "hello!"}')
        await asyncio.sleep(2)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass

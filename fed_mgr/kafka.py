import asyncio
import json
import typing
from logging import Logger

import aiokafka as ak
import sqlmodel
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from fed_mgr.config import Settings, get_settings
from fed_mgr.logger import get_logger

type KafkaSSLContext = dict[str, str | dict[str, str | None]]
type KafkaContext = dict[str, str | dict[str, str | None]]
type KafkaMessage = ak.ConsumerRecord[str, str]
type Callback = typing.Callable[KafkaMessage, None]


class KafkaHandler:
    def __init__(self):
        self._settings: Settings = get_settings()
        ssl_context = self.__create_ssl_context()
        self._consumer_context = self.__create_consumer_context(ssl_context)
        self._producer_context = self.__create_producer_context(ssl_context)
        self._logger: Logger = get_logger(self._settings, "kafka")
        self._tasks: set[asyncio.Task] = set()

    def __del__(self):
        for task in self._tasks:
            if not task.done():
                task.cancel()

    def __create_ssl_context(self) -> KafkaSSLContext | None:
        if self._settings.KAFKA_SSL_CERT_PATH is None:
            return
        return {
            "security_protocol": "SSL",
            "ssl_context": {
                "ssl_cafile": self._settings.KAFKA_SSL_CERT_PATH,
                "ssl_certfile": self._settings.KAFKA_SSL_CERT_PATH,
                "ssl_keyfile": self._settings.KAFKA_SSL_KEY_PATH,
                "ssl_password": self._settings.KAFKA_SSL_PASSWORD,
            },
        }

    def __create_consumer_context(self, ssl_context: KafkaSSLContext | None):
        def deserializer(b: bytes) -> dict[str, str | int | float]:
            return json.loads(b.decode("utf-8"))

        context = {
            "client_id": self._settings.KAFKA_CLIENT_NAME,
            "bootstrap_servers": self._settings.KAFKA_BOOTSTRAP_SERVERS,
            "value_deserializer": deserializer,
            "fetch_max_bytes": self._settings.KAFKA_MAX_REQUEST_SIZE,
            "consumer_timeout_ms": self._settings.KAFKA_TIMEOUT,
            "auto_offset_reset": "earliest",
            "enable_auto_commit": False,
            "group_id": "fed-mgr-group",
            "auto_commit_interval_ms": 1000,
            "max_poll_records": 5,
        }
        if ssl_context:
            context = {**context, **ssl_context}
        return context

    def __create_producer_context(self, ssl_context: KafkaSSLContext | None):
        def serializer(d: dict[str, str | bool | dict[str, str | bool]]):
            return json.dumps(d, sort_keys=True).encode("utf-8")

        context = {
            "client_id": self._settings.KAFKA_CLIENT_NAME,
            "bootstrap_servers": self._settings.KAFKA_BOOTSTRAP_SERVERS,
            "value_serializer": serializer,
            "max_request_size": self._settings.KAFKA_MAX_REQUEST_SIZE,
            "acks": "all",
            "enable_idempotence": True,
        }
        if ssl_context:
            context = {**context, **ssl_context}
        return context

    async def __start_consumer(self, *topic, callback: Callback):
        consumer = AIOKafkaConsumer(*topic, **self._consumer_context)
        await consumer.start()
        try:
            async for message in consumer:
                callback(message)  # must be idempotent
                await consumer.commit()
        finally:
            self._logger.info("Stopping KafkaConsumer")
            await consumer.stop()

    async def __send_one(self, topic: str, message: str):
        producer = AIOKafkaProducer(**self._producer_context)
        await producer.start()
        try:
            await producer.send_and_wait(topic, message, partition=0)
            self._logger.debug("message dispatched")
        finally:
            await producer.stop()

    def __on_task_complete(self, task):
        self._tasks.remove(task)

    def settings(self):
        return self._settings

    def logger(self):
        return self._logger

    def listen_topic(self, *topic, callback: Callback) -> None:
        task = asyncio.create_task(self.__start_consumer(*topic, callback=callback))
        task.add_done_callback(self.__on_task_complete)
        self._tasks.add(task)

    def send(self, topic: str, message: str):
        task = asyncio.create_task(self.__send_one(topic, message))
        task.add_done_callback(self.__on_task_complete)
        self._tasks.add(task)


class KafkaApp:
    def __init__(self, session: sqlmodel.Session | None = None):
        settings = get_settings()
        self._handler = KafkaHandler()
        self._logger = self._handler.logger()
        self._session = session
        self.__listen(settings.KAFKA_EVALUATE_PROVIDERS_TOPIC, self.__on_message)
        self._logger.info("KafkaApp started")

    def __del__(self):
        self._logger.info("KafkaApp exited")

    def __listen(self, topic: str, callback: Callback):
        self._handler.listen_topic(topic, callback=callback)
        self._logger.info("Listening topic %s", topic)

    def __on_message(self, message: KafkaMessage) -> None:
        self._logger.debug(
            "message arrived on topic %s, partition: %s offset: %s, value: %s",
            message.topic,
            message.partition,
            message.offset,
            message.value,
        )

    def send(self, topic: str, message: str):
        self._handler.send(topic, message)


async def main():
    """Start example application."""
    app = KafkaApp()

    while True:
        app.send("evaluate-providers", '{"msg": "hello!"}')
        await asyncio.sleep(2)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass

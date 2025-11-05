import asyncio
from datetime import datetime
import json
import typing
import uuid
from logging import Logger
from typing import Literal, NotRequired

import aiokafka as ak
import sqlmodel
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from fed_mgr.config import Settings, get_settings
from fed_mgr.exceptions import ItemNotFoundError
from fed_mgr.logger import get_logger
from fed_mgr.v1.providers.crud import handle_rally_result

type Serializer = typing.Callable[[typing.Any], bytes]
type Deserializer = typing.Callable[[bytes], dict[str, typing.Any]]
type Callback = typing.Callable[[KafkaMessage], None]


class RallyResult(typing.TypedDict):  # noqa: D101
    msg_version: str
    provider_id: str
    provider_name: str
    provider_type: str
    status: Literal["finished"]
    success: bool
    timestamp: str


class KafkaSSLContext(typing.TypedDict):  # noqa: D101
    security_protocol: str
    ssl_context: dict[str, str | None]


class KafkaConsumerContext(typing.TypedDict):  # noqa: D101
    client_id: str
    bootstrap_servers: str
    value_deserializer: NotRequired[Deserializer]
    fetch_max_bytes: int
    consumer_timeout_ms: int
    auto_offset_reset: Literal["earliest", "latest"]
    enable_auto_commit: bool
    group_id: str
    auto_commit_interval_ms: int
    max_poll_records: int
    security_protocol: NotRequired[str]
    ssl_context: NotRequired[dict[str, str | None] | None]


class KafkaProducerContext(typing.TypedDict):  # noqa: D101
    client_id: str
    bootstrap_servers: str
    value_serializer: Serializer
    max_request_size: int
    acks: str
    enable_idempotence: bool
    security_protocol: NotRequired[str]
    ssl_context: NotRequired[dict[str, str | None] | None]


type KafkaMessage = ak.ConsumerRecord[str, RallyResult]


@typing.final
class KafkaHandler:
    def __init__(self):  # noqa: D107
        self._settings: Settings = get_settings()
        ssl_context = self.__create_ssl_context()
        self._consumer_context = self.__create_consumer_context(ssl_context)
        self._producer_context = self.__create_producer_context(ssl_context)
        self._logger: Logger = get_logger(self._settings, "kafka")
        self._tasks: set[asyncio.Task[None]] = set()

    def __del__(self):
        """Cleanup tasks."""
        for task in self._tasks:
            if not task.done():
                task.cancel()  # pyright: ignore[reportUnusedCallResult]

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

    def __create_consumer_context(
        self, ssl_context: KafkaSSLContext | None
    ) -> KafkaConsumerContext:
        def deserializer(b: bytes) -> dict[str, typing.Any]:
            return json.loads(b.decode("utf-8"))  # pyright: ignore[reportAny]

        context: KafkaConsumerContext = {
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

    def __create_producer_context(
        self, ssl_context: KafkaSSLContext | None
    ) -> KafkaProducerContext:
        def serializer(d: dict[str, str | bool | dict[str, str | bool]]):
            return json.dumps(d, sort_keys=True).encode("utf-8")

        context: KafkaProducerContext = {
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

    async def __start_consumer(self, *topic: str | list[str], callback: Callback):
        consumer = AIOKafkaConsumer(*topic, **self._consumer_context)
        await consumer.start()
        try:
            async for message in consumer:
                try:
                    callback(message)  # must be idempotent
                    await consumer.commit()
                except ItemNotFoundError as e:
                    self._logger.error(e)
                    await consumer.commit()
                except Exception as e:
                    self._logger.error("Error processing message from kafka%s", e)
        finally:
            self._logger.info("Stopping KafkaConsumer")
            await consumer.stop()

    async def __send_one(self, topic: str, message: str | dict[str, typing.Any]):
        producer = AIOKafkaProducer(**self._producer_context)
        await producer.start()
        try:
            await producer.send_and_wait(topic, message, partition=0)
            self._logger.debug("message dispatched")
        finally:
            await producer.stop()

    def __on_task_complete(self, task: asyncio.Task[None]):
        self._tasks.remove(task)

    def settings(self):
        return self._settings

    def logger(self):
        return self._logger

    def listen_topic(self, *topic: str | list[str], callback: Callback) -> None:
        task = asyncio.create_task(self.__start_consumer(*topic, callback=callback))
        task.add_done_callback(self.__on_task_complete)
        self._tasks.add(task)

    def send(self, topic: str, message: str | dict[str, typing.Any]):
        task = asyncio.create_task(self.__send_one(topic, message))
        task.add_done_callback(self.__on_task_complete)
        self._tasks.add(task)


@typing.final
class KafkaApp:
    def __init__(self, session: sqlmodel.Session | None = None, listen: bool = True):
        settings = get_settings()
        self._handler = KafkaHandler()
        self._logger = self._handler.logger()
        self._session = session
        if listen:
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
        if not self._session:
            self._logger.warning("No SQL session available")
            return

        rally_result = message.value
        if not rally_result:
            self._logger.warning("empty message from kafka")
            return

        handle_rally_result(
            session=self._session,
            provider_id=uuid.UUID(rally_result["provider_id"]),
            status=rally_result["status"],
            success=rally_result["success"],
            timestamp=rally_result["timestamp"],
            logger=self._logger,
        )

    def send(self, topic: str, message: dict[str, typing.Any]):
        self._handler.send(topic, message)


async def main():
    """Start example application."""
    settings = get_settings()
    app = KafkaApp(listen=False)

    while True:
        message = {
            "msg_version": "1.0",
            "provider_id": "344c326a-05bf-4e4e-b42b-bb5ed3d99fb3",
            "provider_name": "cnaf",
            "provider_type": "openstack",
            "status": "finished",
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "subtasks": ["task1", "task2"],
        }
        print(message["timestamp"])
        app.send(settings.KAFKA_EVALUATE_PROVIDERS_TOPIC, message)
        await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass

"""Backgound and asynchronous functions used to send data to kafka."""

import asyncio
import json
from logging import Logger
from typing import Any

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import (
    ConsumerStoppedError,
    KafkaConnectionError,
    RecordTooLargeError,
    UnsupportedVersionError,
)

from fed_mgr.config import Settings
from fed_mgr.v1.schemas import (
    KafkaFederationResultsMessage,
    KafkaMonitoringResultsMessage,
)


def add_ssl_parameters(settings: Settings) -> dict[str, Any]:
    """Add SSL configuration parameters for Kafka connection based on provided settings.

    This function constructs a dictionary of SSL-related keyword arguments required for
    secure Kafka communication.

    Args:
        settings (Settings): The settings object containing Kafka SSL configurations.

    Returns:
        dict[str, Any]: A dictionary containing SSL configuration parameters for Kafka.

    Raises:
        ValueError: If the KAFKA_SSL_PASSWORD is None when SSL is enabled.

    """
    if settings.KAFKA_SSL_PASSWORD is None:
        raise ValueError(
            "KAFKA_SSL_PASSWORD can't be None when KAFKA_SSL_ENABLE is True"
        )
    kwargs = {
        "security_protocol": "SSL",
        "ssl_check_hostname": False,
        "ssl_cafile": settings.KAFKA_SSL_CACERT_PATH,
        "ssl_certfile": settings.KAFKA_SSL_CERT_PATH,
        "ssl_keyfile": settings.KAFKA_SSL_KEY_PATH,
        "ssl_password": settings.KAFKA_SSL_PASSWORD,
    }
    return kwargs


def create_kafka_producer(
    settings: Settings, logger: Logger
) -> AIOKafkaProducer | None:
    """Create and configure a KafkaProducer instance based on the provided settings.

    This function sets up a Kafka producer with JSON value serialization, idempotence,
    and other options as specified in the `settings` object. If SSL is enabled, it loads
    the necessary SSL certificates and password from the provided paths.

    Args:
        settings (Settings): Configuration object containing Kafka connection and
            security settings.
        logger (Logger): Logger instance for logging errors and information.

    Returns:
        AIOKafkaProducer: Configured Kafka producer instance.

    """
    kwargs = {
        "client_id": settings.KAFKA_CLIENT_NAME,
        "bootstrap_servers": settings.KAFKA_BOOTSTRAP_SERVERS,
        "value_serializer": lambda x: json.dumps(x, sort_keys=True).encode("utf-8"),
        "max_request_size": settings.KAFKA_MAX_REQUEST_SIZE,
        "acks": "all",
        "enable_idempotence": True,
    }

    try:
        if settings.KAFKA_SSL_ENABLE:
            logger.info("SSL enabled")
            ssl_kwargs = add_ssl_parameters(settings=settings)
            kwargs = {**kwargs, **ssl_kwargs}

        return AIOKafkaProducer(**kwargs)

    except Exception as e:
        msg = f"Failed to create producer: {e.args[0]}"
        logger.error(msg)


async def send(producer: AIOKafkaProducer, topic: str, message: dict[str, Any]) -> None:
    """Send a message to a specified Kafka topic using an asynchronous producer.

    This function starts the given AIOKafkaProducer, sends the provided message to the
    specified topic, and ensures the producer is stopped after the operation, regardless
    of success or failure.

    Args:
        producer (AIOKafkaProducer): The asynchronous Kafka producer instance.
        topic (str): The name of the Kafka topic to send the message to.
        message (dict[str, Any]): The message payload to send.

    Returns:
        None

    Raises:
        Any exceptions raised by producer.start(), producer.send_and_wait(), or
        producer.stop() will propagate.

    """
    await producer.start()
    try:
        await producer.send_and_wait(topic, message)
    finally:
        await producer.stop()


def consume_results_of_federation_tests(message: KafkaFederationResultsMessage) -> None:
    """Consume a Kafka message and processes it based on its topic.

    Logs the received message for debugging purposes. Depending on the topic of the
    message, performs specific actions such as updating request state, storing results,
    or notifying errors. Handles JSON decoding and validation errors by raising
    ValueError with appropriate messages.

    Args:
        message (KafkaFederationResultsMessage): The Kafka message to be consumed.

    """
    # TODO: update request state. Store results


def consume_results_of_monitored_providers(
    message: KafkaMonitoringResultsMessage,
) -> None:
    """Consume a Kafka message and processes it based on its topic.

    Logs the received message for debugging purposes. Depending on the topic of the
    message, performs specific actions such as updating request state, storing results,
    or notifying errors. Handles JSON decoding and validation errors by raising
    ValueError with appropriate messages.

    Args:
        message (KafkaMonitoringResultsMessage): The Kafka message to be consumed.

    """
    # TODO: update request state. Store results


async def consume(
    kafka_consumer: AIOKafkaConsumer, settings: Settings, logger: Logger
) -> None:
    """Consume messages from the Kafka topic.

    Passing each message to the corresponding `consume` function along with the logger.
    Errors during message reading are catched.

    Args:
        kafka_consumer (AIOKafkaConsumer): The registered consumer.
        settings (Settings): Configuration settings for the Kafka consumer.
        logger (Logger): Logger instance for logging information and errors.

    """
    async for message in kafka_consumer:
        try:
            logger.debug("Message: %s", message)
            match message.topic:
                case settings.KAFKA_FEDERATION_TESTS_RESULT_TOPIC:
                    data = KafkaFederationResultsMessage(**message.value)
                    consume_results_of_federation_tests(data, logger)
                case settings.KAFKA_PROVIDERS_MONITORING_TOPIC:
                    data = KafkaMonitoringResultsMessage(**message.value)
                    consume_results_of_monitored_providers(data, logger)
        except ValueError as e:
            msg = f"Failed to consume kafka message on topic: {e.args[0]}"
            logger.error(msg)


async def start_kafka_consumer(topic: str, settings: Settings, logger: Logger) -> None:
    """Start an asynchronous Kafka consumer for the specified topic.

    This function initializes an AIOKafkaConsumer with the given configuration,
    including SSL parameters if enabled. It consumes messages from the Kafka topic.
    Errors during consumer startup or message consumption are logged, and a KafkaError
    is raised if the consumer fails to start.

    Args:
        topic (str): The Kafka topic to consume messages from.
        settings (Settings): Configuration settings for the Kafka consumer.
        logger (Logger): Logger instance for logging information and errors.

    Raises:
        KafkaError: If the Kafka consumer fails to start or during message consumption.

    """
    kwargs = {
        "client_id": settings.KAFKA_CLIENT_NAME,
        "bootstrap_servers": settings.KAFKA_BOOTSTRAP_SERVERS,
        "value_deserializer": lambda x: json.loads(x.decode("utf-8")),
        "fetch_max_bytes": settings.KAFKA_MAX_REQUEST_SIZE,
        "consumer_timeout_ms": settings.KAFKA_TOPIC_TIMEOUT,
        "auto_offset_reset": "earliest",
        "enable_auto_commit": True,
        "group_id": None,
        "max_poll_records": 1,
    }
    if settings.KAFKA_SSL_ENABLE:
        logger.info("SSL enabled")
        ssl_kwargs = add_ssl_parameters(settings)
        kwargs = {**kwargs, **ssl_kwargs}

    kafka_consumer = AIOKafkaConsumer(topic, **kwargs)
    try:
        await kafka_consumer.start()
    except (KafkaConnectionError, UnsupportedVersionError, ValueError) as e:
        msg = f"Failed to start Kafka consumer: {e.args[0]}"
        logger.error(msg)
        return

    msg = f"Consumer on topic '{topic}' started"
    logger.info(msg)

    try:
        await consume(kafka_consumer, settings, logger)
    except (ConsumerStoppedError, RecordTooLargeError) as e:
        msg = f"Error reading messages from topic '{topic}': {e.args[0]}"
        logger.error(msg)
        await kafka_consumer.stop()


async def start_kafka_listeners(
    settings: Settings, logger: Logger
) -> dict[str, asyncio.Task]:
    """Start asynchronous Kafka topic listeners and return a dictionary of tasks.

    Args:
        settings (Settings): Configuration object containing Kafka settings.
        logger (Logger): Logger instance for logging messages.

    Returns:
        dict[str, asyncio.Task]: A dictionary mapping Kafka topic names to their
            corresponding asyncio tasks.

    Raises:
        Any exceptions raised by `start_kafka_consumer` or `asyncio.create_task` will
            propagate.

    """
    logger.info("Start listening on Kafka topics")
    tasks = {}
    # TODO verify message and DB are aligned on startup
    tasks[settings.KAFKA_EVALUATE_PROVIDERS_TOPIC] = asyncio.create_task(
        start_kafka_consumer(settings.KAFKA_EVALUATE_PROVIDERS_TOPIC, settings, logger)
    )
    tasks[settings.KAFKA_FEDERATION_TESTS_RESULT_TOPIC] = asyncio.create_task(
        start_kafka_consumer(
            settings.KAFKA_FEDERATION_TESTS_RESULT_TOPIC, settings, logger
        )
    )
    tasks[settings.KAFKA_PROVIDERS_MONITORING_TOPIC] = asyncio.create_task(
        start_kafka_consumer(
            settings.KAFKA_PROVIDERS_MONITORING_TOPIC, settings, logger
        )
    )
    return tasks


async def stop_kafka_listeners(
    kafka_tasks: dict[str, asyncio.Task], logger: Logger
) -> None:
    """Cancel and await all running Kafka consumer tasks.

    Iterates over the provided dictionary of Kafka consumer tasks, cancels each task,
    and awaits its completion. Logs the cancellation status for each topic.

    Args:
        kafka_tasks (dict[str, asyncio.Task]): A dictionary mapping Kafka topic names
            to their corresponding asyncio tasks.
        logger (Logger): Logger instance for logging cancellation events.

    Returns:
        None

    """
    logger.info("Cancel Kafka consumers")
    for topic, kafka_task in kafka_tasks.items():
        kafka_task.cancel()
        try:
            await kafka_task
        except asyncio.CancelledError:
            msg = f"Kafka consumer on topic '{topic}' cancelled"
            logger.info(msg)
        except Exception as e:
            msg = f"Failed to cancel Kafka consumer on topic '{topic}': {e}"
            logger.error(msg)

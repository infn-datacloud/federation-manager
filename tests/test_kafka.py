"""Unit tests for fed_mgr.kafka module.

This module contains tests for Kafka producer and consumer utilities,
including SSL parameter handling, producer creation, message sending,
and listener management functions.
"""

import asyncio
from unittest import mock

import pytest
from aiokafka.errors import (
    ConsumerStoppedError,
    KafkaConnectionError,
    RecordTooLargeError,
    UnsupportedVersionError,
)

from fed_mgr.kafka import (
    add_ssl_parameters,
    consume,
    create_kafka_producer,
    send,
    start_kafka_consumer,
    start_kafka_listeners,
    stop_kafka_listeners,
)


class DummySettingsSSL:
    """Dummy settings for Kafka SSL parameters used in tests."""

    KAFKA_SSL_PASSWORD = "test_password"
    KAFKA_SSL_CACERT_PATH = "/path/to/cacert"
    KAFKA_SSL_CERT_PATH = "/path/to/cert"
    KAFKA_SSL_KEY_PATH = "/path/to/key"


class DummySettingsProducer:
    """Dummy settings for Kafka producer used in tests."""

    KAFKA_CLIENT_NAME = "test_client"
    KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
    KAFKA_MAX_REQUEST_SIZE = 1048576
    KAFKA_SSL_ENABLE = False
    KAFKA_SSL_PASSWORD = "test_password"
    KAFKA_SSL_CACERT_PATH = "/path/to/cacert"
    KAFKA_SSL_CERT_PATH = "/path/to/cert"
    KAFKA_SSL_KEY_PATH = "/path/to/key"


def test_add_ssl_parameters_returns_correct_dict():
    """Test that add_ssl_parameters returns the correct dict for valid settings."""
    settings = DummySettingsSSL()
    result = add_ssl_parameters(settings)
    assert result == {
        "security_protocol": "SSL",
        "ssl_check_hostname": False,
        "ssl_cafile": "/path/to/cacert",
        "ssl_certfile": "/path/to/cert",
        "ssl_keyfile": "/path/to/key",
        "ssl_password": "test_password",
    }


def test_add_ssl_parameters_raises_value_error_if_password_none():
    """Test add_ssl_parameters raises ValueError when KAFKA_SSL_PASSWORD is None."""
    settings = DummySettingsSSL()
    settings.KAFKA_SSL_PASSWORD = None
    with pytest.raises(ValueError) as excinfo:
        add_ssl_parameters(settings)
    assert "KAFKA_SSL_PASSWORD can't be None" in str(excinfo.value)


def test_create_kafka_producer_no_ssl(monkeypatch):
    """Test producer creation without SSL."""
    settings = DummySettingsProducer()
    logger = mock.Mock()
    mock_producer = mock.Mock()
    monkeypatch.setattr(
        "fed_mgr.kafka.AIOKafkaProducer", lambda **kwargs: mock_producer
    )
    producer = create_kafka_producer(settings, logger)
    assert producer is mock_producer
    logger.info.assert_not_called()


def test_create_kafka_producer_with_ssl(monkeypatch):
    """Test producer creation with SSL enabled."""
    settings = DummySettingsProducer()
    settings.KAFKA_SSL_ENABLE = True
    logger = mock.Mock()
    mock_producer = mock.Mock()
    monkeypatch.setattr(
        "fed_mgr.kafka.AIOKafkaProducer", lambda **kwargs: mock_producer
    )
    monkeypatch.setattr(
        "fed_mgr.kafka.add_ssl_parameters",
        lambda settings: {"security_protocol": "SSL"},
    )
    producer = create_kafka_producer(settings, logger)
    assert producer is mock_producer
    logger.info.assert_called_with("SSL enabled")


def test_create_kafka_producer_exception(monkeypatch):
    """Test producer creation when AIOKafkaProducer raises an exception."""
    settings = DummySettingsProducer()
    logger = mock.Mock()

    def raise_exc(**kwargs):
        raise Exception("fail")

    monkeypatch.setattr("fed_mgr.kafka.AIOKafkaProducer", raise_exc)
    result = create_kafka_producer(settings, logger)
    assert result is None
    logger.error.assert_called()


@pytest.mark.asyncio
async def test_send_calls_producer_methods_in_order():
    """Test that send calls start, send_and_wait, and stop in order."""
    producer = mock.Mock()
    producer.start = mock.AsyncMock()
    producer.send_and_wait = mock.AsyncMock()
    producer.stop = mock.AsyncMock()

    topic = "test_topic"
    message = {"key": "value"}

    await send(producer, topic, message)

    producer.start.assert_awaited_once()
    producer.send_and_wait.assert_awaited_once_with(topic, message)
    producer.stop.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_stops_producer_on_send_and_wait_exception():
    """Test that send stops producer if send_and_wait raises an exception."""
    producer = mock.Mock()
    producer.start = mock.AsyncMock()
    producer.send_and_wait = mock.AsyncMock(side_effect=Exception("fail"))
    producer.stop = mock.AsyncMock()

    topic = "test_topic"
    message = {"key": "value"}

    with pytest.raises(Exception, match="fail"):
        await send(producer, topic, message)

    producer.start.assert_awaited_once()
    producer.send_and_wait.assert_awaited_once_with(topic, message)
    producer.stop.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_stops_producer_on_start_exception():
    """Test that send propagates exception if start fails and does not call stop."""
    producer = mock.Mock()
    producer.start = mock.AsyncMock(side_effect=Exception("fail_start"))
    producer.send_and_wait = mock.AsyncMock()
    producer.stop = mock.AsyncMock()

    topic = "test_topic"
    message = {"key": "value"}

    with pytest.raises(Exception, match="fail_start"):
        await send(producer, topic, message)

    producer.start.assert_awaited_once()
    producer.send_and_wait.assert_not_awaited()
    producer.stop.assert_not_awaited()


@pytest.mark.asyncio
async def test_start_kafka_listeners_creates_tasks(monkeypatch):
    """Test that start_kafka_listeners creates tasks for all topics."""
    settings = mock.Mock()
    settings.KAFKA_EVALUATE_PROVIDERS_TOPIC = "topic1"
    settings.KAFKA_FEDERATION_TESTS_RESULT_TOPIC = "topic2"
    settings.KAFKA_PROVIDERS_MONITORING_TOPIC = "topic3"
    logger = mock.Mock()

    # Mock asyncio.create_task to return a unique mock for each call
    task_mocks = [mock.Mock(name=f"task{i}") for i in range(3)]
    create_task_mock = mock.Mock(side_effect=task_mocks)
    monkeypatch.setattr("fed_mgr.kafka.asyncio.create_task", create_task_mock)
    monkeypatch.setattr("fed_mgr.kafka.start_kafka_consumer", mock.AsyncMock())

    tasks = await start_kafka_listeners(settings, logger)

    assert tasks == {
        "topic1": task_mocks[0],
        "topic2": task_mocks[1],
        "topic3": task_mocks[2],
    }
    logger.info.assert_called_with("Start listening on Kafka topics")
    assert create_task_mock.call_count == 3
    create_task_mock.assert_any_call(mock.ANY)
    # Ensure start_kafka_consumer is called with correct args
    fed_mgr = __import__("fed_mgr.kafka", fromlist=["start_kafka_consumer"])
    fed_mgr.start_kafka_consumer.assert_any_call("topic1", settings, logger)
    fed_mgr.start_kafka_consumer.assert_any_call("topic2", settings, logger)
    fed_mgr.start_kafka_consumer.assert_any_call("topic3", settings, logger)


@pytest.mark.asyncio
async def test_start_kafka_listeners_propagates_exception(monkeypatch):
    """Test that start_kafka_listeners propagates exceptions from create_task."""
    settings = mock.Mock()
    settings.KAFKA_EVALUATE_PROVIDERS_TOPIC = "topic1"
    settings.KAFKA_FEDERATION_TESTS_RESULT_TOPIC = "topic2"
    settings.KAFKA_PROVIDERS_MONITORING_TOPIC = "topic3"
    logger = mock.Mock()

    def raise_exc(*args, **kwargs):
        raise RuntimeError("fail")

    monkeypatch.setattr("fed_mgr.kafka.asyncio.create_task", raise_exc)
    monkeypatch.setattr("fed_mgr.kafka.start_kafka_consumer", mock.AsyncMock())

    with pytest.raises(RuntimeError, match="fail"):
        await start_kafka_listeners(settings, logger)


@pytest.mark.asyncio
async def test_stop_kafka_listeners_cancels_and_awaits_tasks():
    """Test that stop_kafka_listeners cancels and awaits all tasks."""
    logger = mock.Mock()

    # Define dummy coroutines for three topics
    async def dummy_coro():
        await asyncio.sleep(0)

    # Create real asyncio.Task objects
    loop = asyncio.get_running_loop()
    task1 = loop.create_task(dummy_coro())
    task2 = loop.create_task(dummy_coro())
    task3 = loop.create_task(dummy_coro())

    kafka_tasks = {"topic1": task1, "topic2": task2, "topic3": task3}

    await stop_kafka_listeners(kafka_tasks, logger)
    logger.info.assert_any_call("Cancel Kafka consumers")
    for _, task in kafka_tasks.items():
        assert task.cancelled() or task.done()


@pytest.mark.asyncio
async def test_stop_kafka_listeners_logs_cancelled_error():
    """Test that stop_kafka_listeners logs when asyncio.CancelledError is raised."""
    logger = mock.Mock()

    # Create a mock task that raises CancelledError when awaited
    class CancelledTask:
        def cancel(self):
            pass

        def __await__(self):
            raise asyncio.CancelledError()

    kafka_tasks = {"topicX": CancelledTask()}
    await stop_kafka_listeners(kafka_tasks, logger)
    logger.info.assert_any_call("Cancel Kafka consumers")
    logger.info.assert_any_call("Kafka consumer on topic 'topicX' cancelled")


@pytest.mark.asyncio
async def test_stop_kafka_listeners_catches_other_exceptions():
    """Test that stop_kafka_listeners catches exceptions other than CancelledError."""
    logger = mock.Mock()

    class ErrorTask:
        def cancel(self):
            pass

        def __await__(self):
            raise RuntimeError("fail")

    kafka_tasks = {"topicY": ErrorTask()}
    await stop_kafka_listeners(kafka_tasks, logger)
    logger.info.assert_any_call("Cancel Kafka consumers")
    logger.error.assert_any_call(
        "Failed to cancel Kafka consumer on topic 'topicY': fail"
    )


@pytest.mark.asyncio
async def test_start_kafka_consumer_starts_and_consumes(monkeypatch):
    """Test start_kafka_consumer starts consumer and calls consume."""
    settings = mock.Mock()
    settings.KAFKA_CLIENT_NAME = "client"
    settings.KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
    settings.KAFKA_MAX_REQUEST_SIZE = 1000
    settings.KAFKA_TOPIC_TIMEOUT = 100
    settings.KAFKA_SSL_ENABLE = False

    logger = mock.Mock()
    kafka_consumer_mock = mock.Mock()
    kafka_consumer_mock.start = mock.AsyncMock()
    kafka_consumer_mock.stop = mock.AsyncMock()
    monkeypatch.setattr(
        "fed_mgr.kafka.AIOKafkaConsumer", lambda topic, **kwargs: kafka_consumer_mock
    )
    consume_mock = mock.AsyncMock()
    monkeypatch.setattr("fed_mgr.kafka.consume", consume_mock)

    await start_kafka_consumer("topic", settings, logger)
    kafka_consumer_mock.start.assert_awaited_once()
    consume_mock.assert_awaited_once_with(kafka_consumer_mock, settings, logger)
    logger.info.assert_any_call("Consumer on topic 'topic' started")


@pytest.mark.asyncio
async def test_start_kafka_consumer_ssl_enabled(monkeypatch):
    """Test start_kafka_consumer adds SSL parameters when enabled."""
    settings = mock.Mock()
    settings.KAFKA_CLIENT_NAME = "client"
    settings.KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
    settings.KAFKA_MAX_REQUEST_SIZE = 1000
    settings.KAFKA_TOPIC_TIMEOUT = 100
    settings.KAFKA_SSL_ENABLE = True

    logger = mock.Mock()
    kafka_consumer_mock = mock.Mock()
    kafka_consumer_mock.start = mock.AsyncMock()
    kafka_consumer_mock.stop = mock.AsyncMock()
    monkeypatch.setattr(
        "fed_mgr.kafka.AIOKafkaConsumer", lambda topic, **kwargs: kafka_consumer_mock
    )
    monkeypatch.setattr(
        "fed_mgr.kafka.add_ssl_parameters", lambda s: {"ssl_test": True}
    )
    consume_mock = mock.AsyncMock()
    monkeypatch.setattr("fed_mgr.kafka.consume", consume_mock)

    await start_kafka_consumer("topic", settings, logger)
    logger.info.assert_any_call("SSL enabled")
    kafka_consumer_mock.start.assert_awaited_once()
    consume_mock.assert_awaited_once_with(kafka_consumer_mock, settings, logger)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error", [KafkaConnectionError, ValueError, UnsupportedVersionError]
)
async def test_start_kafka_consumer_start_exception(monkeypatch, error):
    """Test start_kafka_consumer raises KafkaError if consumer fails to start."""
    settings = mock.Mock()
    settings.KAFKA_CLIENT_NAME = "client"
    settings.KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
    settings.KAFKA_MAX_REQUEST_SIZE = 1000
    settings.KAFKA_TOPIC_TIMEOUT = 100
    settings.KAFKA_SSL_ENABLE = False

    logger = mock.Mock()
    kafka_consumer_mock = mock.Mock()

    async def start_fail(*args, **kwargs):
        raise error("fail_start")

    kafka_consumer_mock.start = start_fail
    kafka_consumer_mock.stop = mock.AsyncMock()
    monkeypatch.setattr(
        "fed_mgr.kafka.AIOKafkaConsumer", lambda topic, **kwargs: kafka_consumer_mock
    )

    await start_kafka_consumer("topic", settings, logger)
    logger.error.assert_any_call("Failed to start Kafka consumer: fail_start")
    kafka_consumer_mock.stop.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("error", [ConsumerStoppedError, RecordTooLargeError])
async def test_start_kafka_consumer_consume_exception(monkeypatch, error):
    """Test start_kafka_consumer logs and raises KafkaError if consume fails."""
    settings = mock.Mock()
    settings.KAFKA_CLIENT_NAME = "client"
    settings.KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
    settings.KAFKA_MAX_REQUEST_SIZE = 1000
    settings.KAFKA_TOPIC_TIMEOUT = 100
    settings.KAFKA_SSL_ENABLE = False

    logger = mock.Mock()
    kafka_consumer_mock = mock.Mock()
    kafka_consumer_mock.start = mock.AsyncMock()
    kafka_consumer_mock.stop = mock.AsyncMock()
    monkeypatch.setattr(
        "fed_mgr.kafka.AIOKafkaConsumer", lambda topic, **kwargs: kafka_consumer_mock
    )

    async def consume_fail(*args, **kwargs):
        raise error("fail_consume")

    monkeypatch.setattr("fed_mgr.kafka.consume", consume_fail)

    await start_kafka_consumer("topic", settings, logger)
    logger.error.assert_any_call(
        "Error reading messages from topic 'topic': fail_consume"
    )
    kafka_consumer_mock.stop.assert_awaited_once()


@pytest.mark.asyncio
async def test_consume_federation_results(monkeypatch):
    """Test consume processes federation results messages and calls correct consumer."""
    # Prepare mocks
    settings = mock.Mock()
    settings.KAFKA_FEDERATION_TESTS_RESULT_TOPIC = "fed_topic"
    settings.KAFKA_PROVIDERS_MONITORING_TOPIC = "mon_topic"
    logger = mock.Mock()

    message = mock.Mock()
    message.topic = "fed_topic"
    message.value = {"foo": "bar"}

    kafka_consumer = [message]

    # Patch KafkaFederationResultsMessage and consume_results_of_federation_tests
    fed_msg_mock = mock.Mock()
    monkeypatch.setattr(
        "fed_mgr.kafka.KafkaFederationResultsMessage", lambda **kwargs: fed_msg_mock
    )
    consume_fed_mock = mock.Mock()
    monkeypatch.setattr(
        "fed_mgr.kafka.consume_results_of_federation_tests", consume_fed_mock
    )

    async def async_iter(messages):
        for m in messages:
            yield m

    monkeypatch.setattr(
        "fed_mgr.kafka.AIOKafkaConsumer",
        lambda *args, **kwargs: async_iter(kafka_consumer),
    )

    # Patch __aiter__ for the passed kafka_consumer
    class DummyConsumer:
        def __aiter__(self):
            return async_iter(kafka_consumer)

    await consume(DummyConsumer(), settings, logger)

    logger.debug.assert_called_with("Message: %s", message)
    consume_fed_mock.assert_called_once_with(fed_msg_mock, logger)


@pytest.mark.asyncio
async def test_consume_monitoring_results(monkeypatch):
    """Test consume processes monitoring results messages and calls correct consumer."""
    settings = mock.Mock()
    settings.KAFKA_FEDERATION_TESTS_RESULT_TOPIC = "fed_topic"
    settings.KAFKA_PROVIDERS_MONITORING_TOPIC = "mon_topic"
    logger = mock.Mock()

    message = mock.Mock()
    message.topic = "mon_topic"
    message.value = {"baz": "qux"}

    kafka_consumer = [message]

    mon_msg_mock = mock.Mock()
    monkeypatch.setattr(
        "fed_mgr.kafka.KafkaMonitoringResultsMessage", lambda **kwargs: mon_msg_mock
    )
    consume_mon_mock = mock.Mock()
    monkeypatch.setattr(
        "fed_mgr.kafka.consume_results_of_monitored_providers", consume_mon_mock
    )

    async def async_iter(messages):
        for m in messages:
            yield m

    class DummyConsumer:
        def __aiter__(self):
            return async_iter(kafka_consumer)

    await consume(DummyConsumer(), settings, logger)

    logger.debug.assert_called_with("Message: %s", message)
    consume_mon_mock.assert_called_once_with(mon_msg_mock, logger)


@pytest.mark.asyncio
async def test_consume_handles_exception(monkeypatch):
    """Test consume logs error if exception is raised during message processing."""
    settings = mock.Mock()
    settings.KAFKA_FEDERATION_TESTS_RESULT_TOPIC = "fed_topic"
    settings.KAFKA_PROVIDERS_MONITORING_TOPIC = "mon_topic"
    logger = mock.Mock()

    message = mock.Mock()
    message.topic = "fed_topic"
    message.value = {"foo": "bar"}

    kafka_consumer = [message]

    # Patch KafkaFederationResultsMessage to raise exception
    def raise_exc(**kwargs):
        raise ValueError("fail_consume")

    monkeypatch.setattr("fed_mgr.kafka.KafkaFederationResultsMessage", raise_exc)

    async def async_iter(messages):
        for m in messages:
            yield m

    class DummyConsumer:
        def __aiter__(self):
            return async_iter(kafka_consumer)

    await consume(DummyConsumer(), settings, logger)

    logger.error.assert_called_with(
        "Failed to consume kafka message on topic: fail_consume"
    )

"""Kafka adapter for Afra Automation distributed runtime.

This module provides a thin, typed abstraction around Kafka producer and consumer
usage. It is designed for Kubernetes deployments where 50+ bot instances may be
running concurrently and need a durable event backbone with partitions,
consumer-groups, retries, and observability-friendly headers.

The adapter degrades safely when kafka-python is not installed so local
non-Kafka development does not crash at import time.
"""

from __future__ import annotations

import json
import os
import socket
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterable, Iterator, Mapping, Optional


Headers = Dict[str, str]
Payload = Dict[str, Any]


@dataclass(frozen=True)
class KafkaSettings:
    """Configuration for Kafka connectivity and topic naming."""

    bootstrap_servers: str
    client_id: str
    group_id: str
    jobs_topic: str
    retry_topic: str
    dead_letter_topic: str
    auto_offset_reset: str = "earliest"
    enable_auto_commit: bool = False
    request_timeout_ms: int = 30000
    session_timeout_ms: int = 30000
    max_poll_records: int = 100
    security_protocol: str = "PLAINTEXT"

    @classmethod
    def from_env(cls) -> "KafkaSettings":
        """Build settings from environment variables for k8s deployments."""

        instance_id = os.getenv("DIVAR_BOT_INSTANCE_ID", socket.gethostname())
        return cls(
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
            client_id=os.getenv("KAFKA_CLIENT_ID", f"divar-bot-{instance_id}"),
            group_id=os.getenv("KAFKA_GROUP_ID", "afra-divar-bot-workers"),
            jobs_topic=os.getenv("KAFKA_JOBS_TOPIC", "afra.jobs.divar"),
            retry_topic=os.getenv("KAFKA_RETRY_TOPIC", "afra.jobs.divar.retry"),
            dead_letter_topic=os.getenv("KAFKA_DEAD_LETTER_TOPIC", "afra.jobs.divar.dlq"),
            auto_offset_reset=os.getenv("KAFKA_AUTO_OFFSET_RESET", "earliest"),
            enable_auto_commit=os.getenv("KAFKA_ENABLE_AUTO_COMMIT", "false").lower() == "true",
            request_timeout_ms=int(os.getenv("KAFKA_REQUEST_TIMEOUT_MS", "30000")),
            session_timeout_ms=int(os.getenv("KAFKA_SESSION_TIMEOUT_MS", "30000")),
            max_poll_records=int(os.getenv("KAFKA_MAX_POLL_RECORDS", "100")),
            security_protocol=os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
        )


@dataclass(frozen=True)
class QueueEvent:
    """A normalized event envelope used across Kafka and internal workers."""

    event_id: str
    event_type: str
    payload: Payload
    trace_id: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    headers: Headers = field(default_factory=dict)

    def to_bytes(self) -> bytes:
        """Serialize event for Kafka transport."""

        return json.dumps(
            {
                "event_id": self.event_id,
                "event_type": self.event_type,
                "payload": self.payload,
                "trace_id": self.trace_id,
                "created_at": self.created_at,
                "headers": self.headers,
            },
            ensure_ascii=False,
            sort_keys=True,
        ).encode("utf-8")

    @classmethod
    def from_bytes(cls, raw: bytes) -> "QueueEvent":
        """Deserialize event from Kafka bytes."""

        data = json.loads(raw.decode("utf-8"))
        return cls(
            event_id=data["event_id"],
            event_type=data["event_type"],
            payload=data.get("payload", {}),
            trace_id=data.get("trace_id", ""),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            headers=data.get("headers", {}),
        )


class KafkaUnavailable(RuntimeError):
    """Raised when Kafka dependency or broker is not available."""


class KafkaAdapter:
    """Production-oriented Kafka producer/consumer wrapper.

    Responsibilities:
    - publish jobs with trace headers
    - consume jobs through a stable consumer group
    - commit offsets only after successful processing
    - publish failed jobs to retry or dead-letter topics
    """

    def __init__(self, settings: Optional[KafkaSettings] = None) -> None:
        self.settings = settings or KafkaSettings.from_env()
        self._producer = None
        self._consumer = None

    def _load_kafka(self):
        """Import kafka-python lazily."""

        try:
            from kafka import KafkaConsumer, KafkaProducer  # type: ignore
        except Exception as exc:  # pragma: no cover - dependency optional in local env
            raise KafkaUnavailable("kafka-python is not installed") from exc
        return KafkaConsumer, KafkaProducer

    def producer(self):
        """Return a cached Kafka producer."""

        if self._producer is not None:
            return self._producer

        _, KafkaProducer = self._load_kafka()
        self._producer = KafkaProducer(
            bootstrap_servers=self.settings.bootstrap_servers,
            client_id=self.settings.client_id,
            security_protocol=self.settings.security_protocol,
            request_timeout_ms=self.settings.request_timeout_ms,
            value_serializer=lambda value: value,
            key_serializer=lambda value: value.encode("utf-8") if isinstance(value, str) else value,
        )
        return self._producer

    def publish(self, topic: str, event: QueueEvent, key: Optional[str] = None) -> None:
        """Publish an event and wait for broker acknowledgement."""

        producer = self.producer()
        future = producer.send(topic, key=key or event.event_id, value=event.to_bytes())
        future.get(timeout=self.settings.request_timeout_ms / 1000)
        producer.flush()

    def publish_job(self, event: QueueEvent, partition_key: Optional[str] = None) -> None:
        """Publish a job to the main jobs topic."""

        self.publish(self.settings.jobs_topic, event, key=partition_key or event.event_id)

    def publish_retry(self, event: QueueEvent, reason: str) -> None:
        """Publish a retryable event to retry topic with reason header."""

        retry_event = QueueEvent(
            event_id=event.event_id,
            event_type=event.event_type,
            payload=event.payload,
            trace_id=event.trace_id,
            headers={**event.headers, "retry_reason": reason},
        )
        self.publish(self.settings.retry_topic, retry_event, key=event.event_id)

    def publish_dead_letter(self, event: QueueEvent, reason: str) -> None:
        """Publish a poisoned event to dead-letter topic."""

        dlq_event = QueueEvent(
            event_id=event.event_id,
            event_type=event.event_type,
            payload=event.payload,
            trace_id=event.trace_id,
            headers={**event.headers, "dead_letter_reason": reason},
        )
        self.publish(self.settings.dead_letter_topic, dlq_event, key=event.event_id)

    def consumer(self, topics: Optional[Iterable[str]] = None):
        """Return a cached Kafka consumer."""

        if self._consumer is not None:
            return self._consumer

        KafkaConsumer, _ = self._load_kafka()
        self._consumer = KafkaConsumer(
            *(topics or [self.settings.jobs_topic]),
            bootstrap_servers=self.settings.bootstrap_servers,
            client_id=self.settings.client_id,
            group_id=self.settings.group_id,
            auto_offset_reset=self.settings.auto_offset_reset,
            enable_auto_commit=self.settings.enable_auto_commit,
            max_poll_records=self.settings.max_poll_records,
            session_timeout_ms=self.settings.session_timeout_ms,
            request_timeout_ms=self.settings.request_timeout_ms,
            security_protocol=self.settings.security_protocol,
            value_deserializer=lambda value: value,
        )
        return self._consumer

    def consume(self) -> Iterator[QueueEvent]:
        """Yield normalized events from Kafka.

        Offsets are intentionally not auto-committed. The caller must call
        commit() after durable processing has completed.
        """

        consumer = self.consumer()
        for message in consumer:
            yield QueueEvent.from_bytes(message.value)

    def commit(self) -> None:
        """Commit consumed offsets after successful durable processing."""

        if self._consumer is not None:
            self._consumer.commit()

    def close(self) -> None:
        """Close producer and consumer connections."""

        if self._producer is not None:
            self._producer.close()
        if self._consumer is not None:
            self._consumer.close()

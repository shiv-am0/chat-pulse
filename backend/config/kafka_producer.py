import json
import logging
from confluent_kafka import Producer, KafkaException
from django.conf import settings

logger = logging.getLogger(__name__)

_producer_config = {
    'bootstrap.servers': settings.KAFKA_BROKER,
    'acks': 'all',
    'enable.idempotence': True,
    'max.in.flight.requests.per.connection': 5,
    'retries': 3,
    'retry.backoff.ms': 1000,
    'delivery.timeout.ms': 30000,
}

_producer = None


def get_kafka_producer() -> Producer:
    global _producer
    if _producer is None:
        _producer = Producer(_producer_config)
    return _producer


def produce_message(topic: str, key: str, value: dict) -> None:
    producer = get_kafka_producer()

    def delivery_callback(err, msg):
        if err:
            logger.error(f"Kafka delivery failed: {err}")
        else:
            logger.debug(
                f"Delivered to {msg.topic()} "
                f"[{msg.partition()}] @ {msg.offset()}"
            )

    try:
        producer.produce(
            topic=topic,
            key=str(key),
            value=json.dumps(value),
            callback=delivery_callback,
        )
    except BufferError:
        logger.error("Kafka producer queue full — flushing and retrying")
        producer.poll(0)
        try:
            producer.produce(
                topic=topic,
                key=str(key),
                value=json.dumps(value),
                callback=delivery_callback,
            )
        except BufferError:
            raise RuntimeError("Kafka producer queue full — giving up")

    producer.poll(0)

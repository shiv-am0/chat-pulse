import json
import logging
from confluent_kafka import Producer
from django.conf import settings

logger = logging.getLogger(__name__)

_producer_config = {
    'bootstrap.servers': settings.KAFKA_BROKER,
    'acks': 'all',
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
            logger.error(f"Delivery failed: {err}")
        else:
            logger.debug(
                f"Delivered to {msg.topic()} "
                f"[{msg.partition()}] @ {msg.offset()}"
            )

    producer.produce(
        topic=topic,
        key=str(key),
        value=json.dumps(value),
        callback=delivery_callback,
    )
    producer.poll(0)
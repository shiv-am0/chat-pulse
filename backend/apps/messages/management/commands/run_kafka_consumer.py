import json
import logging
import signal
import sys

from confluent_kafka import Consumer, KafkaError, KafkaException
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Runs the Kafka consumer for chat messages'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Kafka consumer...'))

        consumer_config = {
            'bootstrap.servers': settings.KAFKA_BROKER,
            'group.id': 'chat-consumer-group',
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False,
            'max.poll.interval.ms': 300000,
        }

        consumer = Consumer(consumer_config)
        running = True

        def shutdown(signum, frame):
            nonlocal running
            self.stdout.write('\nShutting down consumer gracefully...')
            running = False

        signal.signal(signal.SIGINT, shutdown)
        signal.signal(signal.SIGTERM, shutdown)

        try:
            consumer.subscribe([settings.KAFKA_CHAT_TOPIC])
            self.stdout.write(
                self.style.SUCCESS(
                    f'Subscribed to: {settings.KAFKA_CHAT_TOPIC}'
                )
            )

            while running:
                msg = consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                if msg.error():
                    self._handle_error(msg)
                    continue
                self._process_message(consumer, msg)

        except KafkaException as e:
            logger.error(f"Kafka exception: {e}")
            sys.exit(1)
        finally:
            consumer.close()
            self.stdout.write('Consumer closed.')

    def _handle_error(self, msg):
        if msg.error().code() == KafkaError._PARTITION_EOF:
            self.stdout.write(
                f'End of partition: {msg.topic()} [{msg.partition()}]'
            )
        else:
            logger.error(f'Kafka error: {msg.error()}')

    def _process_message(self, consumer, msg):
        try:
            payload = json.loads(msg.value().decode('utf-8'))
            self.stdout.write(
                f"Processing: room={payload['room_id']} "
                f"from={payload['sender_username']}"
            )

            saved_message = self._save_to_db(payload, msg.offset())
            if saved_message is None:
                consumer.commit(message=msg)
                return

            self._publish_to_redis(payload, saved_message.id)
            consumer.commit(message=msg)

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            consumer.commit(message=msg)
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def _save_to_db(self, payload, kafka_offset):
        from apps.rooms.models import Room
        from apps.users.models import User
        from apps.messages.models import Message

        try:
            room = Room.objects.get(id=payload['room_id'])
        except Room.DoesNotExist:
            logger.warning(f"Room {payload['room_id']} not found. Skipping.")
            return None

        try:
            sender = User.objects.get(id=payload['sender_id'])
        except User.DoesNotExist:
            logger.warning(f"User {payload['sender_id']} not found. Skipping.")
            return None

        message, created = Message.objects.get_or_create(
            kafka_offset=kafka_offset,
            room=room,
            defaults={
                'sender': sender,
                'content': payload['content'],
                'timestamp': parse_datetime(payload['timestamp']),
            }
        )

        if not created:
            logger.info(f"Duplicate at offset {kafka_offset} — skipped.")

        return message

    def _publish_to_redis(self, payload, message_id):
        from apps.rooms import redis_service

        redis_payload = json.dumps({
            'id': message_id,
            'room_id': payload['room_id'],
            'sender_username': payload['sender_username'],
            'content': payload['content'],
            'timestamp': payload['timestamp'],
        })

        redis_service.publish_message(
            room_id=payload['room_id'],
            message=redis_payload
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"  ✓ Published to Redis channel room:{payload['room_id']}"
            )
        )
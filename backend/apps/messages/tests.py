from unittest.mock import patch, MagicMock
from rest_framework import status
from rest_framework.test import APITestCase, override_settings

from apps.users.models import User
from apps.rooms.models import Room, RoomMembership
from apps.messages.models import Message


# Remove throttling for standard auth tests
_NO_AUTH_THROTTLE = {
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {},
}


@override_settings(REST_FRAMEWORK={
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    **_NO_AUTH_THROTTLE,
})
class MessageSendTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="TestPass123!"
        )
        self.other = User.objects.create_user(
            username="other", password="TestPass123!"
        )
        self.client.force_authenticate(user=self.user)

        self.room = Room.objects.create(name="general", creator=self.other)
        RoomMembership.objects.create(user=self.other, room=self.room)
        RoomMembership.objects.create(user=self.user, room=self.room)

        # Mock Redis (used by validate_room_and_membership in rooms/services.py)
        self._patches = {}
        self._mocks = {}
        for name in ("get_cached_room_info", "is_member_of_room",
                     "cache_room_info", "add_member_to_room"):
            p = patch(f"apps.rooms.redis_service.{name}")
            self._patches[name] = p
            self._mocks[name] = p.start()
        self._mocks["get_cached_room_info"].return_value = {"name": "general"}
        self._mocks["is_member_of_room"].return_value = True

        # Mock Kafka producer
        self.kafka_patch = patch("apps.messages.views.produce_message")
        self.mock_kafka = self.kafka_patch.start()

    def tearDown(self):
        for p in self._patches.values():
            p.stop()
        self.kafka_patch.stop()

    def test_send_message_success(self):
        response = self.client.post(
            "/api/messages/send/",
            {"room_id": self.room.id, "content": "Hello!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn("status", response.data)
        self.mock_kafka.assert_called_once()

    def test_send_message_empty_content(self):
        response = self.client.post(
            "/api/messages/send/",
            {"room_id": self.room.id, "content": "   "},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.mock_kafka.assert_not_called()

    def test_send_message_no_room_id(self):
        response = self.client.post(
            "/api/messages/send/",
            {"content": "Hello!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.mock_kafka.assert_not_called()

    def test_send_message_not_member(self):
        self._mocks["is_member_of_room"].return_value = False
        with patch(
            "apps.rooms.services.RoomMembership.objects.filter"
        ) as mock_filter:
            mock_filter.return_value.exists.return_value = False
            response = self.client.post(
                "/api/messages/send/",
                {"room_id": self.room.id, "content": "Hello!"},
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.mock_kafka.assert_not_called()

    def test_send_message_room_not_found(self):
        self._mocks["get_cached_room_info"].return_value = None
        with patch(
            "apps.rooms.services.Room.objects.get",
            side_effect=Room.DoesNotExist,
        ):
            response = self.client.post(
                "/api/messages/send/",
                {"room_id": 9999, "content": "Hello!"},
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.mock_kafka.assert_not_called()


@override_settings(REST_FRAMEWORK={
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    **_NO_AUTH_THROTTLE,
})
class MessageHistoryTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="TestPass123!"
        )
        self.other = User.objects.create_user(
            username="other", password="TestPass123!"
        )
        self.client.force_authenticate(user=self.user)

        self.room = Room.objects.create(name="general", creator=self.other)
        RoomMembership.objects.create(user=self.other, room=self.room)
        RoomMembership.objects.create(user=self.user, room=self.room)

        for i in range(5):
            Message.objects.create(
                room=self.room,
                sender=self.user if i % 2 == 0 else self.other,
                content=f"Message {i}",
            )

    def test_get_messages(self):
        response = self.client.get(
            f"/api/messages/?room_id={self.room.id}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("messages", response.data)
        self.assertEqual(len(response.data["messages"]), 5)

    def test_get_messages_limit(self):
        response = self.client.get(
            f"/api/messages/?room_id={self.room.id}&limit=2"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["messages"]), 2)

    def test_get_messages_before_id(self):
        msgs = list(
            Message.objects.filter(room=self.room).order_by("timestamp")
        )
        before_id = msgs[2].id
        response = self.client.get(
            f"/api/messages/?room_id={self.room.id}&before_id={before_id}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for m in response.data["messages"]:
            self.assertLess(m["id"], before_id)

    def test_get_messages_no_room_id(self):
        response = self.client.get("/api/messages/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_messages_wrong_room(self):
        response = self.client.get("/api/messages/?room_id=9999")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_messages_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(
            f"/api/messages/?room_id={self.room.id}"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class KafkaConsumerTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="TestPass123!"
        )
        self.room = Room.objects.create(name="general", creator=self.user)
        RoomMembership.objects.create(user=self.user, room=self.room)

    def _make_command(self):
        from apps.messages.management.commands.run_kafka_consumer import Command
        return Command()

    def test_save_to_db_creates_message(self):
        cmd = self._make_command()
        payload = {
            "room_id": self.room.id,
            "sender_id": self.user.id,
            "sender_username": "testuser",
            "content": "Hello from Kafka!",
            "timestamp": "2026-04-04T12:00:00Z",
        }
        msg = cmd._save_to_db(payload, kafka_offset=100)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.content, "Hello from Kafka!")
        self.assertEqual(msg.kafka_offset, 100)

    def test_save_to_db_idempotent(self):
        cmd = self._make_command()
        payload = {
            "room_id": self.room.id,
            "sender_id": self.user.id,
            "sender_username": "testuser",
            "content": "Hello!",
            "timestamp": "2026-04-04T12:00:00Z",
        }
        first = cmd._save_to_db(payload, kafka_offset=200)
        second = cmd._save_to_db(payload, kafka_offset=200)
        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        self.assertEqual(first.id, second.id)
        self.assertEqual(Message.objects.filter(kafka_offset=200).count(), 1)

    def test_save_to_db_room_not_found(self):
        cmd = self._make_command()
        payload = {
            "room_id": 9999,
            "sender_id": self.user.id,
            "sender_username": "testuser",
            "content": "Hello!",
            "timestamp": "2026-04-04T12:00:00Z",
        }
        msg = cmd._save_to_db(payload, kafka_offset=300)
        self.assertIsNone(msg)

    def test_save_to_db_user_not_found(self):
        cmd = self._make_command()
        payload = {
            "room_id": self.room.id,
            "sender_id": 9999,
            "sender_username": "ghost",
            "content": "Hello!",
            "timestamp": "2026-04-04T12:00:00Z",
        }
        msg = cmd._save_to_db(payload, kafka_offset=400)
        self.assertIsNone(msg)

    def test_publish_to_redis(self):
        mock_publish = MagicMock()
        with patch(
            "apps.rooms.redis_service.publish_message", mock_publish
        ):
            cmd = self._make_command()
            payload = {
                "room_id": self.room.id,
                "sender_id": self.user.id,
                "sender_username": "testuser",
                "content": "Hello!",
                "timestamp": "2026-04-04T12:00:00Z",
            }
            message = Message.objects.create(
                room=self.room,
                sender=self.user,
                content="Hello!",
                kafka_offset=500,
            )
            cmd._publish_to_redis(payload, message.id)
            mock_publish.assert_called_once()

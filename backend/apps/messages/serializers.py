from rest_framework import serializers
from apps.messages.models import Message
from apps.users.serializers import UserSerializer


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'room', 'sender', 'content', 'timestamp']
        read_only_fields = fields


class SendMessageSerializer(serializers.Serializer):
    room_id = serializers.IntegerField()
    content = serializers.CharField(
        max_length=5000,
        trim_whitespace=True
    )

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "Message content cannot be empty."
            )
        return value

    def validate_room_id(self, value):
        from apps.rooms.models import Room, RoomMembership
        from apps.rooms import redis_service

        # Check room exists — Redis first, DB fallback
        cached_room = redis_service.get_cached_room_info(value)
        if not cached_room:
            try:
                room = Room.objects.get(id=value)
            except Room.DoesNotExist:
                raise serializers.ValidationError("Room not found.")
            redis_service.cache_room_info(
                room.id, room.name, room.creator_id
            )

        # Check membership — Redis first, DB fallback
        request = self.context.get('request')
        if request:
            is_member = redis_service.is_member_of_room(
                value, request.user.id
            )
            if not is_member:
                is_member = RoomMembership.objects.filter(
                    user=request.user,
                    room_id=value
                ).exists()
            if not is_member:
                raise serializers.ValidationError(
                    "You are not a member of this room."
                )
        return value
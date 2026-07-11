from rest_framework import serializers
from apps.messages.models import Message
from apps.users.serializers import UserSerializer
from apps.rooms.services import validate_room_and_membership


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
        request = self.context.get('request')
        if not request:
            return value

        valid, error = validate_room_and_membership(value, request.user)
        if not valid:
            raise serializers.ValidationError(error)
        return value

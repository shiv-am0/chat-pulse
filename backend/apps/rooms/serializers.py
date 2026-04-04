from rest_framework import serializers
from apps.rooms.models import Room, RoomMembership
from apps.users.serializers import UserSerializer


class RoomSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = ['id', 'name', 'creator', 'member_count', 'is_member', 'created_at']
        read_only_fields = fields

    def get_member_count(self, obj):
        return obj.memberships.count()

    def get_is_member(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.memberships.filter(user=request.user).exists()


class RoomCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['name']

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Room name cannot be empty.")
        if len(value) < 3:
            raise serializers.ValidationError(
                "Room name must be at least 3 characters."
            )
        if Room.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError(
                f"A room named '{value}' already exists."
            )
        return value


class RoomMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = RoomMembership
        fields = ['id', 'user', 'joined_at']
        read_only_fields = fields
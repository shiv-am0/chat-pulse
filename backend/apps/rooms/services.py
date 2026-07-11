from apps.rooms.models import Room, RoomMembership
from apps.rooms import redis_service


def validate_room_and_membership(room_id: int, user) -> tuple[bool, str | None]:
    """Check room exists and user is a member. Returns (is_valid, error_message)."""
    cached_room = redis_service.get_cached_room_info(room_id)
    if not cached_room:
        try:
            room = Room.objects.get(id=room_id)
        except Room.DoesNotExist:
            return False, "Room not found."
        redis_service.cache_room_info(room.id, room.name, room.creator_id)

    is_member = redis_service.is_member_of_room(room_id, user.id)
    if not is_member:
        is_member = RoomMembership.objects.filter(
            user=user, room_id=room_id
        ).exists()
    if not is_member:
        return False, "You are not a member of this room."

    return True, None

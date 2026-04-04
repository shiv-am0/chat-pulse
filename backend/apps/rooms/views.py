from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.rooms.models import Room, RoomMembership
from apps.rooms.serializers import (
    RoomSerializer,
    RoomCreateSerializer,
    RoomMembershipSerializer,
)
from apps.rooms import redis_service


class RoomListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rooms = Room.objects.all().select_related('creator')
        serializer = RoomSerializer(
            rooms,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    def post(self, request):
        serializer = RoomCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        room = serializer.save(creator=request.user)
        RoomMembership.objects.create(user=request.user, room=room)
        redis_service.add_member_to_room(room.id, request.user.id)
        redis_service.cache_room_info(room.id, room.name, request.user.id)
        return Response(
            RoomSerializer(room, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )


class RoomDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_room(self, room_id):
        try:
            return Room.objects.get(id=room_id), None
        except Room.DoesNotExist:
            return None, Response(
                {"error": "Room not found."},
                status=status.HTTP_404_NOT_FOUND
            )

    def get(self, request, room_id):
        room, error = self.get_room(room_id)
        if error:
            return error
        memberships = room.memberships.select_related('user').all()
        user_ids = list(memberships.values_list('user_id', flat=True))
        redis_service.sync_room_members_to_redis(room_id, user_ids)
        return Response({
            "room": RoomSerializer(room, context={'request': request}).data,
            "members": RoomMembershipSerializer(memberships, many=True).data
        })


class JoinRoomView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, room_id):
        try:
            room = Room.objects.get(id=room_id)
        except Room.DoesNotExist:
            return Response(
                {"error": "Room not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        already_member = redis_service.is_member_of_room(
            room_id, request.user.id
        )
        if not already_member:
            already_member = RoomMembership.objects.filter(
                user=request.user, room=room
            ).exists()

        if already_member:
            return Response(
                {"error": "You are already in this room."},
                status=status.HTTP_400_BAD_REQUEST
            )

        RoomMembership.objects.create(user=request.user, room=room)
        redis_service.add_member_to_room(room.id, request.user.id)

        return Response(
            {
                "message": f"Joined room '{room.name}' successfully.",
                "room": RoomSerializer(room, context={'request': request}).data
            },
            status=status.HTTP_200_OK
        )


class LeaveRoomView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, room_id):
        try:
            room = Room.objects.get(id=room_id)
        except Room.DoesNotExist:
            return Response(
                {"error": "Room not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            membership = RoomMembership.objects.get(
                user=request.user, room=room
            )
        except RoomMembership.DoesNotExist:
            return Response(
                {"error": "You are not a member of this room."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if room.creator == request.user:
            room_name = room.name
            room_id_copy = room.id
            room.delete()
            redis_service.delete_room_cache(room_id_copy)
            return Response(
                {
                    "message": f"Room '{room_name}' has been deleted "
                               f"because the creator left."
                },
                status=status.HTTP_200_OK
            )

        membership.delete()
        redis_service.remove_member_from_room(room.id, request.user.id)
        return Response(
            {"message": f"Left room '{room.name}' successfully."},
            status=status.HTTP_200_OK
        )
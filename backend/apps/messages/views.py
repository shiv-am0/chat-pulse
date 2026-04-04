import datetime
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.messages.models import Message
from apps.messages.serializers import MessageSerializer, SendMessageSerializer
from config.kafka_producer import produce_message
from django.conf import settings


class SendMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SendMessageSerializer(
            data=request.data,
            context={'request': request}
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        room_id = serializer.validated_data['room_id']
        content = serializer.validated_data['content']

        message_payload = {
            'room_id': room_id,
            'sender_id': request.user.id,
            'sender_username': request.user.username,
            'content': content,
            'timestamp': datetime.datetime.utcnow().isoformat(),
        }

        produce_message(
            topic=settings.KAFKA_CHAT_TOPIC,
            key=str(room_id),
            value=message_payload,
        )

        return Response(
            {
                "status": "Message sent.",
                "message": message_payload
            },
            status=status.HTTP_202_ACCEPTED
        )


class RoomMessagesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        room_id = request.query_params.get('room_id')
        limit = int(request.query_params.get('limit', 50))
        before_id = request.query_params.get('before_id')

        if not room_id:
            return Response(
                {"error": "room_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        from apps.rooms.models import RoomMembership
        if not RoomMembership.objects.filter(
            user=request.user,
            room_id=room_id
        ).exists():
            return Response(
                {"error": "You are not a member of this room."},
                status=status.HTTP_403_FORBIDDEN
            )

        messages = Message.objects.filter(
            room_id=room_id
        ).select_related('sender')

        if before_id:
            messages = messages.filter(id__lt=before_id)

        messages = list(reversed(
            messages.order_by('-timestamp')[:limit]
        ))

        serializer = MessageSerializer(messages, many=True)
        return Response({
            "messages": serializer.data,
            "count": len(serializer.data)
        })
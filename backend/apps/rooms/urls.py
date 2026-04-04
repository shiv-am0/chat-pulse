from django.urls import path
from apps.rooms.views import (
    RoomListCreateView,
    RoomDetailView,
    JoinRoomView,
    LeaveRoomView,
)


urlpatterns = [
    path('', RoomListCreateView.as_view(), name='room-list-create'),
    path('<int:room_id>/', RoomDetailView.as_view(), name='room-detail'),
    path('<int:room_id>/join/', JoinRoomView.as_view(), name='room-join'),
    path('<int:room_id>/leave/', LeaveRoomView.as_view(), name='room-leave'),
]
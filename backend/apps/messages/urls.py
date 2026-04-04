from django.urls import path
from apps.messages.views import SendMessageView, RoomMessagesView


urlpatterns = [
    path('send/', SendMessageView.as_view(), name='message-send'),
    path('', RoomMessagesView.as_view(), name='message-list'),
]
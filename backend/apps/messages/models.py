from django.db import models
from apps.users.models import User
from apps.rooms.models import Room


class Message(models.Model):
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='messages'
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    kafka_offset = models.BigIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'messages'
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['room', 'timestamp']),
        ]

    def __str__(self):
        sender_name = self.sender.username if self.sender else "deleted user"
        return f"{sender_name}: {self.content[:50]}"
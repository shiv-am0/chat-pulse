from django.db import models
from apps.users.models import User


class Room(models.Model):
    name = models.CharField(max_length=100, unique=True)
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_rooms'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'rooms'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} (created by {self.creator.username})"


class RoomMembership(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'room_memberships'
        unique_together = ('user', 'room')

    def __str__(self):
        return f"{self.user.username} in {self.room.name}"
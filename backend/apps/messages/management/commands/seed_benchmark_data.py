import re

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.messages.models import Message
from apps.rooms.models import Room, RoomMembership
from apps.users.models import User


class Command(BaseCommand):
    help = "Create deterministic users, rooms, memberships, and messages for benchmarks"

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=100)
        parser.add_argument("--rooms", type=int, default=10)
        parser.add_argument("--messages", type=int, default=10_000)
        parser.add_argument("--batch-size", type=int, default=1_000)
        parser.add_argument("--message-size", type=int, default=200)
        parser.add_argument("--prefix", default="bench_")
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing rows with this benchmark prefix before seeding",
        )

    def handle(self, *args, **options):
        self._validate_environment()
        self._validate_options(options)

        prefix = options["prefix"]
        existing_users = User.objects.filter(username__startswith=prefix)
        existing_rooms = Room.objects.filter(name__startswith=prefix)

        if (existing_users.exists() or existing_rooms.exists()) and not options["reset"]:
            raise CommandError(
                f"Benchmark rows with prefix {prefix!r} already exist. "
                "Rerun with --reset to replace only those rows."
            )

        with transaction.atomic():
            if options["reset"]:
                # Deleting rooms first cascades their messages and memberships.
                existing_rooms.delete()
                existing_users.delete()

            users = self._create_users(
                prefix=prefix,
                count=options["users"],
                password=settings.BENCHMARK_USER_PASSWORD,
                batch_size=options["batch_size"],
            )
            rooms = self._create_rooms(
                prefix=prefix,
                count=options["rooms"],
                users=users,
                batch_size=options["batch_size"],
            )
            membership_count = self._create_memberships(
                users=users,
                rooms=rooms,
                batch_size=options["batch_size"],
            )
            self._create_messages(
                count=options["messages"],
                message_size=options["message_size"],
                users=users,
                rooms=rooms,
                batch_size=options["batch_size"],
            )

        hot_room_message_count = (
            options["messages"]
            if len(rooms) == 1
            else options["messages"] // 2
        )
        self.stdout.write(self.style.SUCCESS("Benchmark data created."))
        self.stdout.write(f"Users: {len(users)}")
        self.stdout.write(f"Rooms: {len(rooms)}")
        self.stdout.write(f"Memberships: {membership_count}")
        self.stdout.write(f"Messages: {options['messages']}")
        self.stdout.write(f"Hot-room messages: {hot_room_message_count}")
        self.stdout.write(f"BENCHMARK_ROOM_ID={rooms[0].id}")
        self.stdout.write(f"BENCHMARK_USERNAME_PREFIX={prefix}user_")
        self.stdout.write(f"BENCHMARK_USER_COUNT={len(users)}")

    def _validate_environment(self):
        database_name = str(settings.DATABASES["default"]["NAME"])
        if not getattr(settings, "BENCHMARK_MODE", False):
            raise CommandError(
                "Refusing to seed data because BENCHMARK_MODE is not enabled."
            )
        if "benchmark" not in database_name.lower():
            raise CommandError(
                "Refusing to seed data: database name must contain 'benchmark'."
            )
        if not getattr(settings, "BENCHMARK_USER_PASSWORD", ""):
            raise CommandError(
                "BENCHMARK_USER_PASSWORD must be set for disposable benchmark users."
            )

    def _validate_options(self, options):
        if options["users"] < 1:
            raise CommandError("--users must be at least 1.")
        if options["rooms"] < 1:
            raise CommandError("--rooms must be at least 1.")
        if options["messages"] < 0:
            raise CommandError("--messages cannot be negative.")
        if options["batch_size"] < 1:
            raise CommandError("--batch-size must be at least 1.")
        if options["message_size"] < 20 or options["message_size"] > 5_000:
            raise CommandError("--message-size must be between 20 and 5000.")

        prefix = options["prefix"]
        if not re.fullmatch(r"bench_[a-z0-9_]*", prefix):
            raise CommandError(
                "--prefix must start with 'bench_' and contain only lowercase "
                "letters, numbers, or underscores."
            )
        if len(prefix) > 80:
            raise CommandError("--prefix cannot be longer than 80 characters.")

    def _create_users(self, *, prefix, count, password, batch_size):
        # One hash is intentionally shared by disposable benchmark accounts. This
        # keeps seeding fast; these accounts must never be used outside the isolated
        # benchmark database.
        password_hash = make_password(password)
        users = [
            User(
                username=f"{prefix}user_{index:04d}",
                email=f"{prefix}user_{index:04d}@example.invalid",
                password=password_hash,
            )
            for index in range(1, count + 1)
        ]
        return User.objects.bulk_create(users, batch_size=batch_size)

    def _create_rooms(self, *, prefix, count, users, batch_size):
        rooms = [
            Room(
                name=f"{prefix}room_{index:04d}",
                creator=users[(index - 1) % len(users)],
            )
            for index in range(1, count + 1)
        ]
        return Room.objects.bulk_create(rooms, batch_size=batch_size)

    def _create_memberships(self, *, users, rooms, batch_size):
        pending = []
        created = 0
        for room in rooms:
            for user in users:
                pending.append(RoomMembership(room=room, user=user))
                if len(pending) >= batch_size:
                    RoomMembership.objects.bulk_create(pending, batch_size=batch_size)
                    created += len(pending)
                    pending.clear()
        if pending:
            RoomMembership.objects.bulk_create(pending, batch_size=batch_size)
            created += len(pending)
        return created

    def _create_messages(
        self,
        *,
        count,
        message_size,
        users,
        rooms,
        batch_size,
    ):
        hot_room_count = count if len(rooms) == 1 else count // 2
        pending = []

        for index in range(count):
            if index < hot_room_count:
                room = rooms[0]
            else:
                room = rooms[1 + ((index - hot_room_count) % (len(rooms) - 1))]

            prefix = f"Benchmark message {index:08d} "
            content = (prefix + ("x" * message_size))[:message_size]
            pending.append(
                Message(
                    room=room,
                    sender=users[index % len(users)],
                    content=content,
                )
            )

            if len(pending) >= batch_size:
                Message.objects.bulk_create(pending, batch_size=batch_size)
                pending.clear()

        if pending:
            Message.objects.bulk_create(pending, batch_size=batch_size)

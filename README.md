# ChatPulse

A scalable real-time chat platform with a Django REST API backend and a terminal-based CLI client. Messages flow through Kafka for durability, get persisted to PostgreSQL, and are broadcast via Redis Pub/Sub. The CLI uses non-blocking input with a background polling loop for real-time chat.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ChatPulse CLI                            │
│                  (typer + rich + httpx)                         │
│  • select.select non-blocking input   • background poll thread  │
│  • JWT auto-refresh                   • TTY-isolated tokens     │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP + JWT (Bearer)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Django + DRF (backend)                      │
│                                                                 │
│   Auth APIs        Room APIs         Message APIs               │
│   /api/auth/       /api/rooms/       /api/messages/             │
└────────┬───────────────────────────────────┬────────────────────┘
         │                                   │
         ▼                                   ▼
┌─────────────────┐                 ┌─────────────────┐
│   PostgreSQL    │                 │      Kafka      │
│                 │                 │                 │
│  • users        │                 │  chat-messages  │
│  • rooms        │                 │  topic          │
│  • room_memberships               └────────┬────────┘
│  • messages     │                          │
└─────────────────┘                          ▼
         ▲                          ┌─────────────────┐
         │                          │ Kafka Consumer  │
         │ persist                  │ (mgmt command)  │
         └──────────────────────────┤                 │
                                    │ saves to DB     │
                                    │ publishes to    │
                                    │ Redis           │
                                    └────────┬────────┘
                                             │
                                             ▼
                                    ┌─────────────────┐
                                    │      Redis      │
                                    │                 │
                                    │  • Pub/Sub      │
                                    │  • Membership   │
                                    │    cache (Set)  │
                                    │  • Room info    │
                                    │    cache (Hash) │
                                    └─────────────────┘
```

### Message Flow

```
POST /api/messages/send/   (client)
        │
        ▼
  Django validates JWT, room existence (Redis→DB), membership (Redis→DB)
        │
        ▼
  Produce to Kafka topic "chat-messages"  ───── 202 ACCEPTED returned immediately
        │
  ════════════════════════════════════════  async boundary
        │
        ▼
  Kafka Consumer (run_kafka_consumer)
        │
        ├──► Message.objects.get_or_create(kafka_offset=...)  ──► PostgreSQL
        │
        └──► redis_service.publish_message()  ──► Redis Pub/Sub channel room:{id}
```

---

## Tech Stack

| Technology | Version | Purpose |
|---|---|---|
| Python | 3.10+ | Core language |
| Django | 6.0.3 | Web framework |
| Django REST Framework | 3.17.1 | REST API toolkit |
| SimpleJWT | 5.5.1 | JWT authentication |
| PostgreSQL | 15 | Primary database |
| Redis | latest | Caching + Pub/Sub |
| Apache Kafka | 7.4.0 | Message streaming |
| Zookeeper | 7.4.0 | Kafka coordinator |
| Docker + Compose | latest | Infrastructure |
| Typer | 0.12+ | CLI framework |
| Rich | 13+ | Terminal formatting |
| httpx | 0.27+ | HTTP client |

---

## Features

- **JWT Authentication** — register, login, logout, token refresh with blacklist
- **Room Management** — create, list, join, leave rooms with Redis-backed membership
- **Auto-Delete** — room and all messages cascade-deleted when creator leaves
- **Async Messaging** — messages go through Kafka; `202 ACCEPTED` response, consumer persists to DB
- **Idempotent Consumer** — duplicate message protection via `get_or_create` on `kafka_offset`
- **Cursor Pagination** — efficient message history with `before_id`
- **Redis Caching** — room membership (`Set`), room info (`Hash`) with DB fallback
- **Redis Pub/Sub** — real-time message broadcasting to subscribers
- **Terminal CLI** — non-blocking `select.select` input loop, background polling for messages
- **TTY-Isolated Tokens** — each terminal gets its own `~/.chatpulse/token-{tty_hash}`, `chmod 0600`
- **JWT Auto-Refresh** — transparent token refresh on 401 before retrying request
- **Monitoring UIs** — pgAdmin, Kafka UI, RedisInsight included in Docker Compose

---

## Project Structure

```
chatpulse/
│
├── backend/
│   ├── apps/
│   │   ├── users/                   # Auth — register, login, JWT
│   │   │   ├── models.py            #   User(AbstractUser) + is_online
│   │   │   ├── serializers.py       #   Register, User, CustomTokenObtainPair
│   │   │   ├── views.py             #   Register, Login, Logout, Me
│   │   │   ├── urls.py              #   5 endpoints
│   │   │   └── migrations/
│   │   │
│   │   ├── rooms/                   # Rooms — CRUD, membership, auto-delete
│   │   │   ├── models.py            #   Room, RoomMembership
│   │   │   ├── serializers.py       #   Room, RoomCreate, RoomMembership
│   │   │   ├── views.py             #   ListCreate, Detail, Join, Leave
│   │   │   ├── urls.py              #   4 endpoints
│   │   │   ├── redis_service.py     #   All Redis operations (members, info, pub/sub)
│   │   │   └── migrations/
│   │   │
│   │   └── messages/                # Messages — send via Kafka, fetch history
│   │       ├── models.py            #   Message (kafka_offset for idempotency)
│   │       ├── serializers.py       #   Message, SendMessage (with membership check)
│   │       ├── views.py             #   SendMessage (202 Accepted), RoomMessages
│   │       ├── urls.py              #   2 endpoints
│   │       ├── management/
│   │       │   └── commands/
│   │       │       └── run_kafka_consumer.py   # Kafka → DB + Redis Pub/Sub
│   │       └── migrations/
│   │
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py              #   Shared settings (DB, Redis, Kafka, JWT)
│   │   │   ├── local.py             #   Development (DEBUG=True, CORS open)
│   │   │   └── production.py        #   Production (DEBUG=False, ALLOWED_HOSTS)
│   │   ├── __init__.py
│   │   ├── urls.py                  #   Root: admin, api/auth, api/rooms, api/messages
│   │   ├── asgi.py
│   │   ├── wsgi.py
│   │   ├── redis_client.py          #   Connection pool with decode_responses=True
│   │   └── kafka_producer.py        #   Producer singleton with delivery callback
│   │
│   ├── manage.py
│   └── requirements.txt
│
├── cli/
│   ├── pyproject.toml               # Entry point: chatpulse = chatpulse_cli.main:app
│   ├── chatpulse_cli/
│   │   ├── __init__.py
│   │   ├── main.py                  # Typer app with 4 sub-commands + chat command
│   │   ├── config.py                # API URL, poll interval, config dir
│   │   ├── token_storage.py         # TTY-based JWT persistence (token-{hash})
│   │   ├── client.py                # ChatPulseClient — httpx wrapper, JWT auto-refresh
│   │   ├── auth.py                  # register, login, logout, me
│   │   ├── rooms.py                 # list, create, show, join, leave (with confirm)
│   │   ├── messages.py              # send, history (with cursor pagination)
│   │   ├── chat.py                  # Interactive chat: select loop + poll thread
│   │   └── ui.py                    # Rich helpers: table, panel, print_*
│   └── chatpulse_cli.egg-info/
│
├── docker-compose.yml               # PostgreSQL, Redis, Kafka, Zookeeper + UIs
├── .env                             # Environment variables
├── .gitignore
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Docker and Docker Compose
- Git

### 1. Clone

```bash
git clone https://github.com/yourusername/chatpulse.git
cd chatpulse
```

### 2. Start Infrastructure

```bash
docker-compose up -d

# Verify all containers are healthy
docker-compose ps
```

### 3. Backend Setup

Create a virtual environment and install dependencies:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Configure `.env` (already provided — edit as needed):

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `django-insecure-...` | Django secret key |
| `DEBUG` | `True` | Debug mode |
| `DB_NAME` | `chatpulse` | PostgreSQL database name |
| `DB_USER` | `admin` | PostgreSQL user |
| `DB_PASSWORD` | `password` | PostgreSQL password |
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection string |
| `KAFKA_BROKER` | `localhost:9092` | Kafka bootstrap server |

Run migrations and start:

```bash
python manage.py migrate
python manage.py runserver
```

In a separate terminal, start the Kafka consumer:

```bash
cd backend
source .venv/bin/activate
python manage.py run_kafka_consumer
```

### 4. CLI Setup

```bash
cd cli
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

The `chatpulse` command is now available:

```bash
chatpulse --help
```

### 5. Try it

```bash
# Register a user
chatpulse auth register alice alice@example.com

# Login
chatpulse auth login alice

# Create a room
chatpulse rooms create general

# List rooms
chatpulse rooms list

# Show room details
chatpulse rooms show 1

# Send a message
chatpulse messages send 1 "Hello, world!"

# View history
chatpulse messages history 1

# Enter interactive chat
chatpulse chat 1
```

Open a second terminal, register/login as a second user, join the same room, and run `chatpulse chat 1` in both — messages appear in real time via polling.

---

## API Reference

### Authentication — `/api/auth/`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/register/` | ❌ | Register a new user |
| POST | `/login/` | ❌ | Login, returns access + refresh tokens, sets `is_online=true` |
| POST | `/logout/` | ✅ | Blacklists refresh token, sets `is_online=false` |
| POST | `/token/refresh/` | ❌ | Refresh access token |
| GET | `/me/` | ✅ | Get current user profile |

### Rooms — `/api/rooms/`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/` | ✅ | List all rooms with member count and membership status |
| POST | `/` | ✅ | Create room (auto-join creator, caches in Redis) |
| GET | `/<id>/` | ✅ | Room details + members (syncs Redis membership cache) |
| POST | `/<id>/join/` | ✅ | Join a room (checks Redis→DB for duplicate) |
| POST | `/<id>/leave/` | ✅ | Leave a room; if creator, deletes room + all messages |

### Messages — `/api/messages/`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/send/` | ✅ | Send message (validates membership via Redis→DB, produces to Kafka, returns 202) |
| GET | `/?room_id=<id>` | ✅ | Get message history (latest first, reversed for chronological) |
| GET | `/?room_id=<id>&limit=20` | ✅ | Limit results |
| GET | `/?room_id=<id>&before_id=50` | ✅ | Cursor-based pagination (messages with `id < before_id`) |

---

## CLI Reference

### Global Options

| Flag | Env Var | Description |
|---|---|---|
| `--api-url` | `CHATPULSE_API_URL` | Override API base URL (default: `http://localhost:8000/api`) |
| `--verbose`, `-v` | — | Enable verbose output |

### `chatpulse auth`

| Command | Description |
|---|---|
| `register <username> <email>` | Register a new account (password prompted) |
| `login <username>` | Login (password prompted), stores JWT in `~/.chatpulse/token-{tty}` |
| `logout` | Logout and clear stored tokens |
| `me` | Show current user profile |

### `chatpulse rooms`

| Command | Description |
|---|---|
| `list` | List all rooms with member count and join status |
| `create <name>` | Create a new room (min 3 characters) and auto-join |
| `show <id>` | Show room details and member list |
| `join <id>` | Join a room |
| `leave <id>` | Leave a room; confirms before deleting if creator |

### `chatpulse messages`

| Command | Description |
|---|---|
| `send <room_id> <content>` | Send a message to a room |
| `history <room_id> [--limit] [--before-id]` | Show message history with cursor pagination |

### `chatpulse chat`

| Command | Description |
|---|---|
| `chat <room_id>` | Enter interactive chat mode |

**Interactive commands** (while in chat mode):

| Command | Description |
|---|---|
| `/q` | Quit chat |
| `/help` | Show available commands |
| Any other text | Send as a message to the room |

Messages from other users appear automatically via a background polling thread (default 2s interval). Customize with `CHATPULSE_POLL_INTERVAL` env var.

---

## Database Schema

```text
users
├── id                          (PK, BigAutoField)
├── password                    (hashed)
├── last_login
├── is_superuser
├── username                    (unique, 150 chars)
├── first_name
├── last_name
├── email
├── is_staff
├── is_active
├── date_joined
├── is_online                   (BooleanField, default=false)
└── created_at                  (DateTimeField, auto_now_add)

rooms
├── id                          (PK, BigAutoField)
├── name                        (CharField 100, unique)
├── creator_id                  (FK → users, CASCADE)
└── created_at                  (DateTimeField, auto_now_add)

room_memberships
├── id                          (PK, BigAutoField)
├── user_id                     (FK → users, CASCADE)
├── room_id                     (FK → rooms, CASCADE)
└── joined_at                   (DateTimeField, auto_now_add)
UNIQUE: (user_id, room_id)

messages
├── id                          (PK, BigAutoField)
├── room_id                     (FK → rooms, CASCADE)
├── sender_id                   (FK → users, SET_NULL, nullable)
├── content                     (TextField)
├── timestamp                   (DateTimeField, auto_now_add)
└── kafka_offset                (BigIntegerField, nullable)
INDEX: (room_id, timestamp)
DB_TABLE: messages
ORDERING: timestamp
```

---

## Redis Data Structures

| Key | Type | Example | Purpose |
|---|---|---|---|
| `room:{id}:members` | Set | `{"1", "2", "3"}` | Room membership cache (O(1) lookups) |
| `room:{id}:info` | Hash | `{name: "general", creator_id: "1"}` | Room metadata cache (TTL: 3600s) |
| `room:{id}` | Channel | — | Pub/Sub channel for real-time messages |

---

## Token Storage

Tokens are stored per-terminal, not globally, so multiple users can log in on different terminals without interfering:

| File | Mechanism |
|---|---|
| `~/.chatpulse/token-{hash}` | `os.ttyname(0)` → MD5[:8] → `chmod 0600` |

The suffix is derived from the terminal device path (`/dev/pts/1`, etc.), meaning each terminal window gets its own isolated token file. No shared state, no env vars needed.

---

## Docker Services

| Service | Image | Ports | UI | Purpose |
|---|---|---|---|---|
| PostgreSQL | postgres:15 | 5432 | — | Primary database |
| Redis | redis/redis-stack:latest | 6379, 8001 | localhost:8001 | Cache + Pub/Sub + RedisInsight |
| Kafka | confluentinc/cp-kafka:7.4.0 | 9092 | localhost:8080 (via kafka-ui) | Message broker |
| Zookeeper | confluentinc/cp-zookeeper:7.4.0 | 2181 | — | Kafka coordinator |
| Kafka UI | provectuslabs/kafka-ui:latest | 8080 | localhost:8080 | Kafka monitoring |
| pgAdmin | dpage/pgadmin4:latest | 5050 | localhost:5050 | PostgreSQL admin |

### Monitoring Credentials

| Dashboard | URL | Credentials |
|---|---|---|
| pgAdmin | http://localhost:5050 | `admin@chatpulse.com` / `password` |
| Kafka UI | http://localhost:8080 | — |
| RedisInsight | http://localhost:8001 | — |

---

## Key Design Decisions

### Why Kafka instead of writing directly to DB?

Kafka decouples message ingestion from persistence. Django returns `202 ACCEPTED` immediately without waiting for DB writes. Messages are never lost even if PostgreSQL is temporarily unavailable. The consumer can batch, retry, and reprocess on restart.

### Why Redis for membership checks?

Membership checks happen on every message send request. Redis `SISMEMBER` is `O(1)` and avoids hitting PostgreSQL on every send. The Serializer checks Redis first, falls back to DB on cache miss, and `RoomDetailView` syncs the cache on read.

### Why `on_delete=CASCADE` on Room → Message?

When the room creator leaves, the entire room is deleted. PostgreSQL cascades the delete through memberships and messages in a single atomic transaction — no manual cleanup code needed.

### Why manual Kafka offset commit?

`enable.auto.commit=False` ensures the offset is only committed after the message is successfully saved to PostgreSQL and published to Redis. If the consumer crashes mid-processing, the message is re-processed on restart — guaranteed at-least-once delivery.

### Why `get_or_create` with `kafka_offset`?

If the consumer crashes after saving to DB but before committing the offset, it re-processes the same message on restart. `get_or_create(kafka_offset=offset, ...)` with `defaults={...}` prevents duplicate messages in the database — the duplicate path only logs and skips.

### Why `select.select` for CLI input instead of `input()`?

`input()` blocks the entire thread until Enter is pressed. `select.select([sys.stdin], [], [], 0.2)` returns every 200ms, allowing the polling thread's messages to be displayed without waiting for user input. This enables real-time message display while the user is reading or idle.

### Why TTY-based token isolation?

Each terminal window gets its own `~/.chatpulse/token-{tty_hash}` file based on `os.ttyname(0)`. This means two people can authenticate as different users on the same machine (different terminals) without overwriting each other's tokens. No explicit `--user` flag needed, no shared state.

---

## Environment Variables

| Variable | Default | Used By |
|---|---|---|
| `CHATPULSE_API_URL` | `http://localhost:8000/api` | CLI — API base URL |
| `CHATPULSE_POLL_INTERVAL` | `2` | CLI — polling interval in seconds |
| `SECRET_KEY` | *(required)* | Backend — Django secret key |
| `DEBUG` | `False` | Backend — debug mode |
| `DB_NAME` | — | Backend — PostgreSQL database |
| `DB_USER` | — | Backend — PostgreSQL user |
| `DB_PASSWORD` | — | Backend — PostgreSQL password |
| `DB_HOST` | `localhost` | Backend — PostgreSQL host |
| `DB_PORT` | `5432` | Backend — PostgreSQL port |
| `REDIS_URL` | `redis://localhost:6379` | Backend — Redis connection |
| `KAFKA_BROKER` | `localhost:9092` | Backend — Kafka bootstrap |

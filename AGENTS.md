# Chat Pulse Repository Guide

## Purpose and components

Chat Pulse is a terminal-oriented chat system:

- `backend/` is the Django 6 / Django REST Framework API.
- `cli/` is the installable Typer + HTTPX client (`chatpulse`).
- PostgreSQL is the system of record for users, rooms, memberships, and messages.
- Kafka is the asynchronous boundary for submitted messages.
- `run_kafka_consumer` persists Kafka records and publishes Redis Pub/Sub events.
- Redis also caches room metadata and membership sets. The CLI does not subscribe to
  Redis; interactive chat polls the message-history HTTP endpoint.
- `docker-compose.yml` and `deploy/` retain the local/retired VPS container topology.
  `.github/workflows/deploy.yml` now runs backend CI and an image build only. The target
  hosted path is Northflank services/PostgreSQL plus Aiven and Upstash.

Read [docs/architecture.md](docs/architecture.md) before changing a cross-component
flow, [docs/engineering-risks.md](docs/engineering-risks.md) before reliability work,
and [docs/deployment-runbook.md](docs/deployment-runbook.md) before release work. Use
[docs/free-tier-deployment.md](docs/free-tier-deployment.md) for first provisioning.
Follow [docs/credential-remediation.md](docs/credential-remediation.md) for the known
tracked production-environment credential exposure.

## Source map and entry points

- `backend/manage.py`: Django command entry point.
- `backend/config/settings/{base,local,test,production}.py`: environment settings.
- `backend/config/urls.py`: root API routes and `/api/health/`.
- `backend/apps/users/`: registration, JWT login/refresh/logout, current user.
- `backend/apps/rooms/`: room lifecycle, membership, and Redis helpers.
- `backend/apps/messages/`: send/history APIs, message model, Kafka consumer.
- `backend/config/kafka_{config,producer}.py`: shared broker config and producer.
- `cli/chatpulse_cli/main.py`: CLI root command.
- `cli/chatpulse_cli/client.py`: HTTP/JWT client and refresh behavior.
- `cli/chatpulse_cli/chat.py`: interactive input plus HTTP polling thread.
- `backend/entrypoint.sh`: API migrations followed by Gunicorn; an explicit command
  bypasses migrations and runs directly (used by the consumer).

The messages app has Django label `chat_messages` to avoid collision with
`django.contrib.messages`; use that label in migration dependencies and commands.

## Supported runtimes and setup

The backend image and CI use Python 3.12. Django 6 requires Python 3.12 or newer.
The CLI package declares Python 3.10 or newer. Do not describe the whole repository
as Python 3.10-compatible.

Host-run backend with containerized infrastructure:

```bash
cp .env.example .env
docker compose --profile local up -d postgres redis zookeeper kafka

cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

The example environment uses host-facing `localhost` service addresses and the
local Compose PostgreSQL credentials. Keep `.env` untracked. In another activated
backend shell, start the consumer:

```bash
python manage.py run_kafka_consumer
```

Local CLI development:

```bash
cd cli
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
CHATPULSE_API_URL=http://localhost:8000/api chatpulse --help
```

The CLI defaults to the production API. Set `CHATPULSE_API_URL` explicitly during
local development. Published installation is `pipx install chatpulse-cli`.
The package build and tag-triggered upload path is documented in
[docs/pypi-release.md](docs/pypi-release.md).

The current Compose file is not a turnkey full-local application stack: Nginx
expects host TLS certificate paths, while `.env.example` uses host-facing database,
Redis, and Kafka addresses. Use the infrastructure-only command above unless the
Compose networking and TLS configuration have deliberately been prepared.

## Checks that exist

Run backend checks from `backend/` in an activated environment. With a configured
`.env`:

```bash
DJANGO_SETTINGS_MODULE=config.settings.test python manage.py test
DJANGO_SETTINGS_MODULE=config.settings.test python manage.py check
DJANGO_SETTINGS_MODULE=config.settings.test python manage.py makemigrations --check --dry-run
```

`config.settings.test` replaces PostgreSQL with in-memory SQLite, replaces the
Django Redis cache with local memory, and disables DRF throttling. Application tests
also mock Kafka and most direct Redis calls. Passing tests do not prove PostgreSQL,
Kafka, Redis, Docker, Nginx, or end-to-end delivery.

There is currently no configured linter, formatter, type checker, coverage gate, or
CLI test suite. Do not invent commands for them. If adding one, keep the toolchain
small, document it here, and put it in CI.

Useful container checks after `.env` exists:

```bash
docker compose --profile local config --quiet
docker compose --profile local ps
```

## Architecture and dependency rules

- Keep DRF views thin when logic is reused or coordinates dependencies; do not add
  service/repository layers for straightforward ORM operations.
- Serializers own request-shape and field validation. Views own HTTP status and
  orchestration. Models and database constraints own durable invariants.
- PostgreSQL is authoritative. Redis must not become the sole authority for room
  existence or authorization.
- Keep CLI behavior compatible with existing API paths and status codes. Preserve
  15-second HTTP timeouts, useful nonzero exits, JWT refresh, and non-interactive
  configuration through environment variables.
- Avoid importing network clients in ways that connect during module import. Tests
  and management commands must be importable without running external services.

## Database and migrations

- Use Django migrations for every model or constraint change; never edit an applied
  migration to change production state.
- Preserve table names `users`, `rooms`, `room_memberships`, and `messages` unless a
  staged production migration explicitly requires a rename.
- Room names are unique, memberships are unique on `(user, room)`, deleting a room
  cascades memberships/messages, and deleting a sender leaves messages with a null
  sender.
- Inspect generated SQL/locking implications for production changes and run
  `makemigrations --check --dry-run` after tests.
- SQLite tests do not validate PostgreSQL-specific constraints or query plans. Add a
  PostgreSQL integration test when the behavior depends on PostgreSQL semantics.

## Kafka and Redis expectations

Current Kafka behavior is at-least-once consumption, not exactly once:

- The API keys records by room ID, which preserves per-room order only while all
  records for that room resolve to the same partition.
- Producer `acks=all` and idempotence are configured, but `produce_message()` only
  enqueues and polls callbacks. A `202` does not currently prove broker acknowledgement.
- The consumer disables auto-commit and commits after database persistence plus
  Redis publication. A crash can replay a record.
- The current database deduplication key is Kafka offset alone. Offsets are only
  unique within `(topic, partition)`, so do not rely on this for multi-partition
  correctness until the schema includes topic and partition or a stable message ID.
- Missing rooms/users and malformed JSON are committed and dropped. Other malformed
  payloads can retry indefinitely; there is no dead-letter path.
- A Redis publication failure leaves the Kafka offset uncommitted; after recovery,
  the existing database row can be published again. Redis Pub/Sub is ephemeral.

For changes to this path, test broker unavailability, delivery acknowledgement,
duplicates, partition identity, malformed records, retry limits, poison records,
database/Redis partial failure, ordering, lag, and restart behavior. State the exact
user-visible delivery semantics.

Redis calls currently propagate connection errors. DB fallback occurs on cache
misses, not Redis outages. Any new degradation policy must keep authorization based
on PostgreSQL and make cache updates best-effort or repairable without masking DB
failures.

## API, authentication, and security

- All endpoints require JWT except register, login, token refresh, and health.
- Access tokens live for one hour; refresh tokens live for seven days; logout
  blacklists the supplied refresh token.
- Enforce room membership on message send and history. Add object-level authorization
  tests whenever room or message access changes.
- Validate query parameters through serializers or explicit guarded parsing; client
  mistakes must return 4xx, not uncaught `ValueError`/invalid slicing errors.
- Never log JWTs, passwords, SASL credentials, connection URLs containing secrets,
  or environment values. Use key names and redacted values in diagnostics.
- `deploy/.env.production` is currently tracked and contains credential-like production
  values. Never display or copy its values. Treat its Django, database, and embedded
  Redis credentials as exposed; rotate them before removing the file and coordinating
  an authorized Git-history cleanup. `.gitignore` is prepared to ignore it once it is
  untracked. See `docs/credential-remediation.md`.
- `deploy/aiven-ca.pem` is a tracked public CA certificate, not a private key. Do not
  replace it with client certificates or private keys.

## Testing expectations

- Add a regression test before or with every bug fix.
- Cover success, validation, unauthenticated, unauthorized/cross-user, and important
  dependency-failure paths appropriate to the change.
- Mock at the external boundary, then assert both the response and durable effects.
  Do not make implementation-mirroring mocks the only evidence for reliability work.
- Run focused app tests first, then the complete backend suite and migration check.
- For CLI changes, add a test harness rather than relying only on manual Rich output.
- For messaging or deployment changes, add an integration/smoke check or clearly
  report why external services were not exercised.

## Observability and error handling

- Use the existing Python logging configuration; do not use ad-hoc prints in request
  code. The management command may use `self.stdout` for operator progress.
- Include safe identifiers such as room, topic, partition, offset, and message ID in
  async-path logs; never include secrets or full message contents.
- Catch exceptions only when the caller receives a deliberate response or the
  process has a defined retry/drop policy. Do not silently convert dependency
  failures into success.
- `/api/health/` checks PostgreSQL only. Do not treat it as proof that Kafka, Redis,
  the consumer, or end-to-end messaging is healthy.

## Git and deployment safety

- Preserve unrelated user changes. Do not reset, stash, mass-format, commit, push,
  merge, tag, rewrite history, or deploy unless explicitly requested.
- A push to `master` triggers backend CI. Once Northflank continuous deployment is
  enabled, the same push can also change the public backend; treat it as a deployment
  action requiring explicit authorization.
- A `v*` tag triggers the PyPI publish workflow for the CLI.
- The retired EC2 SSH/GHCR deployment has been removed from the workflow. Northflank
  owns builds and deployments once its two combined services are provisioned. Record
  the exact Northflank build commit for release and rollback.
- The API entrypoint runs migrations before Gunicorn. Review migration compatibility
  and backup/restore readiness before deployment.
- Follow the preflight, health, log, smoke-test, and rollback steps in
  `docs/deployment-runbook.md`. CI success alone is not production verification.

## Completion and teaching

After meaningful work, report the result, runtime/data flow, important files and
interfaces, design trade-offs, failure/security implications, exact checks and
outcomes, and remaining uncertainty. Distinguish unit-tested behavior from external
integration and production verification. Explain enough that the maintainer can
reason about retries, consistency, authorization, migrations, and rollback without
the AI.

# Free-tier deployment guide

This is the target deployment for the ChatPulse hobby/demo environment after the AWS
EC2 instance was terminated. It preserves the Django, Kafka, Redis, and PostgreSQL
application architecture; only the hosting and configuration change.

Free plans can change, suspend idle workloads, enforce quotas, and provide no SLA.
This design is appropriate for learning and a low-traffic portfolio deployment, not a
business-critical production system.

## Selected services

| Component | Provider | Why it fits | Important free-tier limit |
|---|---|---|---|
| Django API | Northflank Sandbox | One always-on container with public HTTPS and custom-domain support | Counts as one of two free services |
| Kafka consumer | Northflank Sandbox | A second always-on container can run the management command | Uses the second free service |
| PostgreSQL | Northflank Sandbox add-on | Included database on the same private project network | Uses the one free add-on; limited sandbox resources |
| Kafka | Aiven Free | Managed Kafka with standard clients and SASL/TLS | Small-workload limits, no SLA, idle services may power off |
| Redis | Upstash Free | Redis protocol, TLS, and Pub/Sub support | 256 MB and 500,000 commands/month |
| Static site/installers | Vercel | Already hosts `docs/` and the custom domain | Existing deployment remains unchanged |
| CLI package | PyPI | Already publishes `chatpulse-cli` | Publishing remains separate from backend deployment |

Northflank is preferred to Render because ChatPulse needs a continuously polling Kafka
consumer as well as an HTTP service. Render free web services sleep after inactivity,
and its free PostgreSQL expires. Railway is not selected because its no-cost starting
credit is time-limited and continued use has a monthly minimum.

Provider references:

- [Northflank pricing](https://northflank.com/pricing)
- [Northflank Docker deployment](https://northflank.com/docs/v1/application/getting-started/build-and-deploy-your-code)
- [Northflank PostgreSQL add-on](https://northflank.com/docs/v1/application/databases-and-persistence/deploy-databases-on-northflank/deploy-postgresql-on-northflank)
- [Aiven Kafka free tier](https://aiven.io/docs/products/kafka/free-tier/kafka-free-tier)
- [Aiven Kafka SASL configuration](https://aiven.io/docs/products/kafka/howto/kafka-sasl-auth)
- [Upstash Redis pricing](https://upstash.com/pricing/redis)

## Credential safety precondition

Do not reuse any value from `deploy/.env.production`. That file is present in Git
history and must be treated as exposed. Create every database, Kafka, Redis, and Django
credential from scratch. Store deployment values in a Northflank secret group, not in
GitHub variables or a committed `.env` file.

After the replacement stack is verified, follow
[credential-remediation.md](credential-remediation.md) to untrack the old file and plan
an authorized history cleanup. Removing the current file alone does not revoke exposed
credentials.

## Provision the managed dependencies

Choose provider regions close to the Northflank service region where possible.

### 1. Northflank project and PostgreSQL

1. Create a Northflank **Developer Sandbox** project named `chatpulse` in a region near
   the selected Kafka and Redis regions.
2. Create a PostgreSQL add-on named `chatpulse-postgres`, with database name
   `chatpulse`, TLS enabled, one replica, and the free resource plan.
3. Keep the add-on private. The API and consumer are in the same Northflank project and
   do not need a public database endpoint.
4. Link the standard application connection details—not the admin account—to the
   `chatpulse-production` secret group described below. Alias the fields to the names
   the Django settings expect.

The application uses `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD`
rather than `DATABASE_URL`. Use the Northflank CLI's secure port forwarding for local
administration instead of exposing PostgreSQL publicly.

### 2. Aiven Kafka

1. Create an **Aiven for Apache Kafka Free** service.
2. Enable `kafka_authentication_methods.sasl`.
3. Keep `SCRAM-SHA-256` enabled.
4. Enable `letsencrypt_sasl` and select the SASL endpoint that uses the public CA. This
   lets the container use its system trust store; do not set `KAFKA_SSL_CA_LOCATION`.
5. Create the `chat-messages` topic with **one partition**.
6. Record the SASL host and port as one `host:port` value, plus the service username and
   password.

One partition is intentional. The current message table deduplicates on Kafka offset
alone, although offsets are unique only within a topic partition. Multiple partitions
can incorrectly collide until the schema stores topic and partition too.

If `letsencrypt_sasl` is unavailable in the selected Aiven location, download only the
project CA certificate, mount it into both Northflank containers as a runtime secret
file, and set `KAFKA_SSL_CA_LOCATION` to that absolute mount path. Do not commit a new
CA, client certificate, or private key to this repository.

### 3. Upstash Redis

1. Create a free Redis database.
2. Copy the TLS **Redis/TCP** connection URL, not the REST API URL.
3. Confirm the URL starts with `rediss://` and store the entire credential-bearing URL
   as `REDIS_URL` in Northflank.

Redis is used both for Django caching and Pub/Sub. The application currently propagates
Redis connection failures, so an Upstash outage can affect room operations and Kafka
consumer progress.

## Create the Northflank secret group

Create one runtime-only secret group named `chatpulse-production` and link it to both
services. Fill these values in the Northflank dashboard. Values below are descriptions,
not shell-ready credentials.

| Variable | Value or source |
|---|---|
| `SECRET_KEY` | New random value of at least 64 characters; Northflank supports `${fn.randomSecret(64)}` |
| `DEBUG` | `False` |
| `DJANGO_SETTINGS_MODULE` | `config.settings.production` |
| `ALLOWED_HOSTS` | Northflank-generated API hostname plus `localhost`; later add `api.chatpulse.online` |
| `CORS_ALLOWED_ORIGINS` | `https://chatpulse.online` |
| `CSRF_TRUSTED_ORIGINS` | `https://chatpulse.online` |
| `DB_NAME` | Northflank add-on database name (linked/aliased secret) |
| `DB_USER` | Northflank standard application user (linked/aliased secret) |
| `DB_PASSWORD` | Northflank standard application password (linked/aliased secret) |
| `DB_HOST` | Northflank internal PostgreSQL host (linked/aliased secret) |
| `DB_PORT` | Northflank internal PostgreSQL port (linked/aliased secret) |
| `REDIS_URL` | Upstash `rediss://` TCP URL |
| `KAFKA_BROKER` | Aiven public-CA SASL `host:port` |
| `KAFKA_SECURITY_PROTOCOL` | `SASL_SSL` |
| `KAFKA_SASL_MECHANISM` | `SCRAM-SHA-256` |
| `KAFKA_SASL_USERNAME` | Aiven service username |
| `KAFKA_SASL_PASSWORD` | Aiven service password |
| `GUNICORN_WORKERS` | `1` for the free container size |
| `GUNICORN_TIMEOUT` | `120` |
| `GUNICORN_LOG_LEVEL` | `info` |
| `SECURE_SSL_REDIRECT` | `True` |
| `SECURE_HSTS_SECONDS` | `31536000` after HTTPS/custom-domain verification; use `0` during initial hostname validation |

Omit `KAFKA_SSL_CA_LOCATION` when using Aiven's public CA. The topic name is currently
fixed to `chat-messages` in Django settings; a `KAFKA_CHAT_TOPIC` environment variable
does not override it.

For local production-connectivity testing only, copy `.env.example` to the ignored
root `.env`, replace its placeholders from the provider dashboards, and run
`chmod 600 .env`. Do not use that local file as the deployment secret store.

## Deploy the two Northflank services

Connect the GitHub repository to Northflank, create a project, and create the API before
the consumer. Use the repository's `master` branch only after the intended diff is
reviewed and the GitHub checks pass.

### API combined service: `chatpulse-api`

- Build type: Dockerfile
- Repository branch: `master`
- Build context: `/backend`
- Dockerfile path: `/backend/Dockerfile`
- Runtime: default Docker entrypoint and command
- Secret group: `chatpulse-production`
- Public HTTP port: `8000`
- Instances: `1`
- Health check: TCP on port `8000`, with enough initial delay for the first migration

Use `/api/health/` after deployments to verify the private PostgreSQL add-on. The
platform TCP probe is only liveness; it does not check PostgreSQL, Kafka, Redis, or the
consumer.

### Consumer combined service: `chatpulse-consumer`

- Build type, branch, context, Dockerfile, and secret group: same as the API
- Public ports: none
- Instances: `1`
- Docker command override: `python manage.py run_kafka_consumer`

The image entrypoint executes an explicit command directly, so the consumer does not
run migrations. Start it only after the API has successfully run migrations once.

Northflank combined services can automatically build and deploy commits from the linked
branch. Keep continuous integration enabled but continuous deployment disabled: after
the repository's GitHub checks pass, manually deploy that exact commit to the API and
then the consumer. The GitHub workflow does not SSH to the terminated EC2 instance.
If automatic deployment is enabled later, every push to `master` becomes immediately
production-impacting and the independent Northflank deployment will not wait for the
GitHub test result.

## Domain cutover

1. Verify the Northflank-generated API URL first.
2. Add `api.chatpulse.online` as a custom domain on the API service.
3. Replace the old EC2 `api` DNS record with the exact CNAME target Northflank shows.
4. Wait for Northflank TLS issuance and verify the certificate and hostname.
5. Update `ALLOWED_HOSTS` to include both the custom and generated hostnames during
   cutover. Keep the generated hostname for emergency checks.
6. Confirm the CLI still targets `https://api.chatpulse.online/api`.

DNS and custom-domain changes are external production-impacting actions and require
explicit approval immediately before execution.

## Verification

Record the deployed Git commit and complete these checks without logging credentials:

1. GitHub backend CI and image build succeed.
2. API build and deployment logs show migrations completed and Gunicorn bound to 8000.
3. `GET /api/health/` returns 200 and reports the database as `ok` on the generated URL,
   then on the custom domain.
4. The consumer log shows subscription to `chat-messages` without repeated SASL/TLS
   errors.
5. Register and log in with a disposable test user.
6. Create/join a test room, submit a uniquely identifiable message, verify the API
   returns 202, then verify the message appears in history.
7. Confirm the consumer did not repeatedly process the message and review Northflank,
   Aiven, and Upstash usage dashboards.
8. Verify `curl -fsSL https://chatpulse.online/install.sh` and PowerShell installer
   headers/content after the Vercel site redeploys.

The health endpoint proves PostgreSQL connectivity only. The message round trip is the
required proof for Kafka and the consumer. Redis Pub/Sub has no durable delivery and is
not exercised by the CLI, which polls the history API.

## Rollback

Before each release, record the currently healthy Northflank build commit for both
services. If the new release fails and has no incompatible database migration:

1. Disable continuous deployment.
2. Redeploy the prior healthy build to both API and consumer.
3. Re-run the database health and end-to-end message checks.
4. Re-enable continuous deployment only after the failure is understood.

Do not reverse a migration or restore PostgreSQL data without reviewing data-loss
impact and obtaining explicit authorization. Free plans are not a backup strategy;
export data before risky schema work.

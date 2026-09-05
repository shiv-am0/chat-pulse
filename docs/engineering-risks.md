# Engineering risk register

Assessment date: 2026-09-05. Severity is user/production impact; likelihood is based on
the current implementation, not observed production incident data.

| Priority | Risk | Severity | Likelihood | Effort | Evidence and next action |
|---|---|---:|---:|---:|---|
| P0 | Production credentials are tracked in Git | Critical | High | Medium | `deploy/.env.production` exists in current Git and prior commits. Redacted inspection confirmed a non-placeholder Django secret, database password, and credential-bearing Redis URL. Rotate first, then untrack and perform coordinated history cleanup; follow `credential-remediation.md`. |
| P0 | Message API returns `202` before Kafka acknowledges delivery | High | Medium | Medium | `produce_message()` enqueues then `poll(0)`; callback failure is log-only. Define the acceptance contract, wait for delivery or introduce a durable outbox, and test broker timeout/unavailability. |
| P0 | Consumer deduplication uses Kafka offset without topic/partition | High | Medium | Medium | `Message.kafka_offset` is globally unique, but Kafka offsets are partition-scoped. Migrate to `(topic, partition, offset)` or a producer-generated stable message ID before using multiple partitions. |
| P0 | Replacement hosting is not yet provisioned or externally verified | High | High | Medium | EC2 is terminated and the repository now has CI only. Provision the documented Northflank/Aiven/Upstash target, verify the full message path, and record the first rollback point. |
| P1 | Redis errors can cause partial success and HTTP 500 | High | High | Medium | Room create/join/leave update PostgreSQL before Redis without a degradation policy; send authorization calls Redis before DB fallback. Keep PostgreSQL authoritative, use transactions for DB invariants, and make cache repair explicit. |
| P1 | Poison Kafka payloads can retry indefinitely | High | Medium | Medium | Only invalid JSON is committed/dropped. Missing/type-invalid fields raise on each replay; there is no retry budget or dead-letter topic. Add schema validation, failure classification, metrics, and a DLQ policy. |
| P1 | Baseline tests do not exercise real infrastructure | Medium | High | Medium | The 40 tests use SQLite and mocks for Redis/Kafka. Add PostgreSQL integration tests, then a Compose-based message-path smoke test. |
| P1 | Query parameters can produce server errors | Medium | High | Low | Room/message `limit` and message `before_id` use unguarded conversion/slicing. Validate with DRF serializers and cover malformed, zero, negative, and oversized values. |
| P1 | Current Compose is not a turnkey local full stack | Medium | High | Medium | Nginx requires host TLS files; API service uses production settings; `.env.example` is for host-facing infrastructure. Split local and production overrides or document a supported profile. |
| P2 | Redis Pub/Sub has no repository subscriber | Medium | High | Medium | Consumer publishes events, but CLI polls HTTP and no WebSocket/SSE gateway exists. Remove unused publication or add a justified delivery component; do not call it client real-time delivery today. |
| P2 | Room mutations lack explicit consistency boundaries | Medium | Medium | Medium | Creator room creation and membership creation are separate writes; cache failures occur after DB changes. Add `transaction.atomic()` where multiple DB writes form one invariant and reconcile cache after commit. |
| P2 | Health check covers PostgreSQL only | Medium | High | Low | `/api/health/` can be green while producer, consumer, or Redis is unavailable. Keep liveness cheap; add separate readiness/operational signals and consumer-lag monitoring. |
| P2 | CLI has no automated tests | Medium | Medium | Medium | Auth refresh, token storage, timeouts, polling, exit codes, and Windows/TTY behavior are unverified in CI. Add Typer/HTTPX boundary tests before expanding CLI behavior. |
| P2 | Dependency and action update controls are absent | Medium | Medium | Low | Requirements are pinned, but no automated vulnerability/update review is configured and GitHub Actions use floating major tags. Add a modest dependency review/update policy. |

## Recommended sequence

1. Rotate the exposed credentials, untrack the production env file, and coordinate
   authorized history cleanup using `credential-remediation.md`.
2. Provision and verify the replacement hosting, then record commit-based Northflank rollback.
3. Fix query validation as a small, well-contained API reliability change.
4. Define the message acceptance guarantee, then correct producer acknowledgement and
   partition-aware consumer identity together with migrations and tests.
5. Make Redis explicitly best-effort for caching while preserving database-backed
   authorization and consistent DB mutations.
6. Add PostgreSQL and broker/Redis integration coverage before claiming production
   readiness for failure recovery.
7. Add readiness, consumer lag, error-rate, and end-to-end message delivery signals.

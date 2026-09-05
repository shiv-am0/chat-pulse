# Production deployment runbook

The EC2/VPS deployment is retired. The target hobby deployment is two Northflank
combined services and a PostgreSQL add-on, with Aiven Kafka and Upstash Redis. Provisioning
and first-deployment instructions are in
[free-tier-deployment.md](free-tier-deployment.md).

This runbook does not authorize a deployment. Once Northflank continuous deployment is
enabled, a push to `master` can change the public backend and requires explicit owner
approval.

## Active credential incident

`deploy/.env.production` is tracked in current and historical Git commits. Redacted
inspection confirms credential-like Django, database, and Redis values. Treat them as
exposed, do not reuse them for the new stack, and follow
[credential-remediation.md](credential-remediation.md). Never paste values into issues,
chat, logs, commands, or commits.

## Release mechanism

- `.github/workflows/deploy.yml` is now a backend CI workflow. It runs Django checks,
  tests, migration-drift detection, and a local Docker image build. It does not publish
  an image or contact the terminated EC2 instance.
- Northflank combined services build from `backend/Dockerfile` on the linked `master`
  branch. Keep continuous deployment disabled and manually deploy the exact commit that
  passed GitHub CI, first to the API and then to the consumer.
- The API image entrypoint applies migrations before Gunicorn starts. The consumer's
  command override bypasses migrations and runs `python manage.py run_kafka_consumer`.
- Northflank configuration is external to Git. Record service settings and the deployed
  commit in each release note; never record secret values.

## Preconditions

Before requesting approval, record:

1. Intended Git commit SHA and reviewed diff.
2. GitHub backend CI, installer CI when applicable, and Docker build results.
3. Migration operations, expected locks/runtime, compatibility, and a tested backup or
   export procedure for schema changes.
4. Required configuration key names with values redacted.
5. Current healthy Northflank build/commit for both API and consumer.
6. Expected user impact, rollback trigger, and observation window.

Run locally from `backend/` with the test settings:

```bash
python manage.py check --settings=config.settings.test
python manage.py makemigrations --check --dry-run --settings=config.settings.test
python manage.py test --settings=config.settings.test
```

Also review `git diff --check`, the complete intended diff, and tracked files for env
files, private keys, client certificates, tokens, or passwords.

## Deployment

After explicit approval, push the reviewed commit to `master` or manually deploy that
exact commit in Northflank. Observe GitHub CI and both Northflank builds. Deploy the API
first when a migration is required; allow it to become healthy before replacing or
restarting the consumer.

## Post-deploy verification

Capture timestamps and evidence for:

1. Public TLS and `GET https://api.chatpulse.online/api/health/` returning HTTP 200.
2. API and consumer running without restart loops.
3. Logs free of migration, PostgreSQL, Kafka, Redis, and authentication errors; redact
   sensitive payloads.
4. Registration/login or an authorized disposable test-account flow.
5. Room authorization.
6. A uniquely identifiable message returning 202 and later appearing in history.
7. No repeated consumer error or duplicate visible message.
8. Northflank, Aiven, and Upstash quota/usage state.

The health endpoint checks PostgreSQL only. A green CI build and HTTP 200 do not prove
that Kafka, Redis, or the consumer path works.

## Rollback

If a release fails:

1. Disable Northflank continuous deployment and record the first failure signal/time.
2. Decide whether the cause is application, configuration, dependency, or schema.
3. For an application-only compatible change, redeploy the recorded prior healthy
   build to API and consumer.
4. Restore prior service configuration if configuration caused the failure.
5. Reverse a migration only when its reverse operation was reviewed as safe. Otherwise
   deploy a forward-compatible fix. Restore data only with explicit owner authorization.
6. Repeat the health and end-to-end message checks before re-enabling deployment.

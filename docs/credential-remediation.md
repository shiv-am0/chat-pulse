# Tracked credential remediation

## Confirmed exposure

`deploy/.env.production` is tracked at `HEAD` and appears in commits dating from
2026-07-11. A value-safe inspection (names/classification only) confirmed:

- a non-placeholder Django `SECRET_KEY`;
- a non-placeholder PostgreSQL `DB_PASSWORD`;
- a Redis URL containing embedded credentials; and
- a non-empty Kafka SASL account identifier.

The Kafka SASL password was not confirmed as a real credential by the redacted check,
but it must be verified directly by the credential owner. No private-key PEM marker was
found in repository history. `deploy/aiven-ca.pem` is an X.509 public CA certificate,
not a private key.

Assume confirmed credentials were exposed to everyone and every automation identity
with repository read access. Deleting the current file or making the repository private
does not revoke copied credentials or remove earlier blobs.

## Safe remediation order

This plan requires explicit authorization and access to the external providers/VPS.
Do not execute history rewriting or credential changes as an incidental code edit.

1. Identify the PostgreSQL and Redis providers, affected database/user, applications,
   deployment hosts, and owners. Confirm whether Kafka credentials in the file are live.
2. Create replacement credentials in the provider secret stores with least privilege.
   For PostgreSQL, prefer a new application role/password so old and new can overlap.
3. Update the VPS `/opt/chatpulse/.env` through the approved secret channel. Never pass
   secret values on a command line that will be logged or retained in shell history.
4. Recreate API and consumer containers, then verify database access, Redis access,
   authentication, and an end-to-end uniquely identifiable message.
5. Revoke the old PostgreSQL and Redis credentials. Rotate Kafka credentials too if the
   value is live or its status is uncertain.
6. Rotate Django `SECRET_KEY`. This can invalidate signed Django state and may affect
   JWT validation; plan a forced re-login and verify token behavior.
7. Review provider access/audit logs from 2026-07-11 onward for unexpected use. Preserve
   evidence according to the owner's incident-response policy.
8. Remove `deploy/.env.production` from Git tracking while preserving the required local
   VPS file. The repository `.gitignore` already ignores `.env.*` except `.env.example`.
9. Inventory forks, clones, pull-request refs, Actions artifacts/caches, and mirrors.
   Coordinate a `git filter-repo` (or provider-supported sensitive-data removal) rewrite
   with all contributors, then force-update affected refs only with explicit approval.
10. Re-scan all reachable refs for the old secrets using value hashes or provider tools,
    without printing the values. Rotation remains mandatory even after a clean scan.

## Verification evidence

The incident can be closed only when the owner records:

- rotation/revocation timestamps and responsible provider-side identities;
- successful production health and end-to-end message checks using new credentials;
- failure of the revoked credentials;
- a current-tree and reachable-history scan with no credential values;
- repository/fork/cache cleanup status and any residual exposure; and
- the decision on user session/token invalidation after Django key rotation.

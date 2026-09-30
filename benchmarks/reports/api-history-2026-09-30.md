# Authenticated message-history API benchmark — 2026-09-30

## Result

The locally verified operating point is **150 authenticated requests/second for
three minutes**, completing **27,000 requests** with **0% application errors**, **no
dropped iterations**, **18.73 ms p50**, **28.22 ms p95**, and **54.76 ms p99**
client-observed latency.

This is a local benchmark result for the configuration below, not a claim about
production capacity.

## Workload and pass criteria

- Endpoint: `GET /api/messages/?room_id=1&limit=50`
- Flow: k6 -> Gunicorn/Django -> JWT authentication -> PostgreSQL membership check
  -> PostgreSQL message query -> serialization -> k6
- Executor: k6 constant arrival rate
- Identities: 50 seeded users with independently obtained JWT access tokens
- Dataset: 100 users, 10 rooms, 1,000 memberships, and 10,000 messages; the queried
  hot room contained 5,000 messages
- Product throttling: enabled
- Required thresholds: error rate below 1%, p95 below 500 ms, p99 below 1,000 ms,
  and zero dropped iterations
- Requests/sec calculation: completed endpoint requests divided by the configured
  measurement duration; the 50 setup logins are excluded

## Environment

| Component | Configuration |
|---|---|
| Host | Intel Core i7-1065G7, 4 cores / 8 threads, 15 GiB RAM |
| OS | Linux 7.2.5-3-omarchy x86_64 |
| Application | Python 3.12.14, Gunicorn 23.0, 4 synchronous workers |
| Database | PostgreSQL 15 container, 512 MiB container memory limit |
| Redis | Redis Stack container, 256 MiB container memory limit; used by DRF throttling |
| Load generator | k6 2.3.0 on the same host as the application |
| Source | Base commit `3934ea8` plus the uncommitted benchmark harness |

Each independent run used a fresh Redis logical database so setup logins did not
inherit anonymous-login throttle state. Redis data was not flushed. The PostgreSQL
dataset remained identical across runs.

## Measurements

All latency values are milliseconds and contain only calls to the endpoint under
test, not setup logins.

| Target RPS | Duration | Completed | Achieved RPS | p50 | p95 | p99 | Error rate | Dropped | Interpretation |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 10 | 30 s | 300 | 10.00 | 14.13 | 18.03 | 21.93 | 0.000% | 0 | Smoke pass |
| 25 | 60 s | 1,500 | 25.00 | 13.19 | 17.59 | 37.81 | 0.000% | 0 | Pass |
| 50 | 60 s | 3,001 | 50.02 | 12.09 | 21.38 | 41.52 | 0.000% | 0 | Pass |
| 100 | 60 s | 6,001 | 100.02 | 14.64 | 25.70 | 48.45 | 0.000% | 0 | Pass |
| 150 | 60 s | 9,001 | 150.02 | 11.89 | 23.35 | 48.95 | 0.000% | 0 | Pass |
| 150 | 180 s | 27,000 | 150.00 | 18.73 | 28.22 | 54.76 | 0.000% | 0 | Stability pass |
| 175 | 60 s | 10,501 | 175.02 | 58.95 | 232.52 | 282.32 | 0.000% | 0 | Passed, but near the latency knee |
| 175 | 180 s | 31,480 | 174.89 | 42.25 | 493.50 | 617.31 | 0.000% | 20 | Failed zero-drop criterion |
| 200 | 60 s | 9,279 | 154.65 | 1,888.75 | 2,309.31 | 2,477.87 | 0.000% | 2,722 | Overloaded; latency and drop thresholds failed |

The 200-RPS run scheduled 12,001 iterations but completed 9,279 and dropped 2,722.
This demonstrates why a 0% HTTP error rate is not sufficient evidence of capacity:
work that the load generator cannot start must be considered alongside responses.

## Interpretation

- **150 RPS is the defensible local result.** It passed the three-minute
  confirmation without errors or drops and retained low tail latency.
- **175 RPS is near saturation.** The one-minute run completed, but its p95 was
  already 8.3 times the three-minute 150-RPS p95. During the longer confirmation it
  also dropped work.
- **200 RPS is beyond this configuration's useful capacity.** Completed throughput
  fell to 154.65 RPS while p95 exceeded 2.3 seconds and 2,722 iterations were
  dropped.
- The practical performance knee for this exact local setup is therefore between
  150 and 175 RPS. A production target should include additional headroom rather
  than operate at that knee.

## Suggested resume wording

> Built a reproducible k6 benchmark for an authenticated Django/PostgreSQL message
> history API; sustained 150 requests/sec for 3 minutes (27,000 requests) with
> 28 ms p95, 55 ms p99, 0% errors, and zero dropped requests using four Gunicorn
> workers against a 10K-message local dataset.

Keep the words “local dataset” or otherwise name the environment. Do not present
this as production traffic or distributed-system throughput.

## Reports

- [150 RPS, three-minute confirmation](../results/product-r150-180s-confirmation-api-report.html)
- [175 RPS, three-minute near-saturation run](../results/product-r175-180s-confirmation-api-report.html)
- [200 RPS overload run](../results/product-r200-60s-api-report.html)
- The remaining HTML, JSON, and CSV artifacts are in `benchmarks/results/` and are
  intentionally ignored by Git because they can be large and machine-specific.

## Limitations and next improvements

- k6 and the application shared one host, so they competed for CPU and memory.
- The measurements cover one read-only endpoint, one hot room, and a warm local
  database; they do not measure message production, Kafka, the consumer, Redis
  publication, or end-to-end persistence.
- Only the 150- and 175-RPS boundary points received longer confirmation runs. For
  statistically stronger claims, repeat the confirmation at least three times and
  report the median plus variability.
- No CPU, memory, PostgreSQL connection, query, or disk time series were captured.
- The local path excludes real network latency, TLS, Nginx, and production service
  limits.

For the commands and report format, see [`../README.md`](../README.md).

# Chat Pulse API benchmarks

This first benchmark measures the authenticated message-history endpoint:

```text
k6 -> Gunicorn/Django -> JWT authentication -> membership query
   -> PostgreSQL message query -> DRF serialization -> k6
```

It reports:

- achieved requests per second;
- p50, p95, and p99 client-observed latency; and
- the percentage of requests that returned an unexpected result.

Kafka and Redis are not on this read path. They will require separate benchmarks.

The first measured local capacity sweep is documented in
[`reports/api-history-2026-09-30.md`](reports/api-history-2026-09-30.md).

## What the numbers mean

- **Requests/sec** is completed history requests divided by the configured measured
  duration. Setup logins are excluded from both the count and the duration.
- **p50** is the median: half the requests were faster and half were slower.
- **p95** is the latency experienced by all but the slowest 5% of requests.
- **p99** highlights the slowest 1%, which averages often hide.
- **Error rate** counts non-200 responses, transport failures, and responses without
  the expected `messages` array.
- **Dropped iterations** are requests k6 intended to start but could not schedule.
  They are not completed-request errors, but a valid capacity run requires zero.

The script uses k6's constant-arrival-rate executor. If `RATE=50`, k6 attempts to
start 50 requests every second. When the API cannot keep up, latency rises, errors
appear, or k6 reports dropped iterations.

## 1. Install prerequisites

Use Python 3.12 for the backend. Install the backend and benchmark Python packages
inside the backend virtual environment:

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -r ../benchmarks/requirements.txt
cd ..
```

Install k6 using the package for your Linux distribution, then verify it:

```bash
k6 version
```

## 2. Start infrastructure and create an isolated database

The repository's supported local path runs infrastructure in containers and the
backend on the host:

```bash
docker compose --profile local up -d postgres redis zookeeper kafka
docker compose --profile local ps
```

Create the benchmark database once:

```bash
docker compose --profile local exec postgres \
  createdb -U admin chatpulse_benchmark
```

The command reports an error if the database already exists; that is harmless.

Run migrations:

```bash
cd backend
DB_NAME=chatpulse_benchmark \
DJANGO_SETTINGS_MODULE=config.settings.benchmark \
python manage.py migrate
```

The benchmark settings refuse to start unless the database name contains the word
`benchmark`.

## 3. Seed deterministic data

Still inside `backend/`:

```bash
DB_NAME=chatpulse_benchmark \
BENCHMARK_USER_PASSWORD='<choose-a-disposable-password>' \
DJANGO_SETTINGS_MODULE=config.settings.benchmark \
python manage.py seed_benchmark_data \
  --users 100 \
  --rooms 10 \
  --messages 10000
```

The command prints values similar to:

```text
BENCHMARK_ROOM_ID=1
BENCHMARK_USERNAME_PREFIX=bench_user_
BENCHMARK_USER_COUNT=100
```

Save the room ID for the load-test command. To rebuild the same prefixed dataset,
add `--reset`. Reset deletes only prefixed benchmark rows, and only while benchmark
settings and a benchmark-named database are active.

`BENCHMARK_USER_PASSWORD` is required and is intentionally not stored in the
repository. Use a disposable value that is never used by a real account.

## 4. Start a production-style API process

The Django development server is not suitable for performance measurements. Run
Gunicorn from `backend/`:

```bash
DB_NAME=chatpulse_benchmark \
BENCHMARK_USER_PASSWORD='<same-disposable-password>' \
DJANGO_SETTINGS_MODULE=config.settings.benchmark \
gunicorn config.wsgi:application \
  --bind 127.0.0.1:8000 \
  --workers 4 \
  --timeout 120 \
  --access-logfile -
```

Leave this terminal running.

## 5. Run a smoke benchmark

In another terminal, from the repository root:

```bash
ROOM_ID=1 \
BENCH_PASSWORD='<same-disposable-password>' \
RATE=10 \
DURATION=30s \
BENCH_USER_COUNT=10 \
PRE_ALLOCATED_VUS=10 \
MAX_VUS=20 \
./benchmarks/run_api_benchmark.sh
```

Replace `ROOM_ID=1` with the value printed by the seed command.

The defaults are:

| Variable | Default | Meaning |
|---|---:|---|
| `API_URL` | `http://localhost:8000/api` | API under test |
| `BENCH_PASSWORD` | required | Password assigned while seeding |
| `RATE` | `20` | Requests k6 attempts to start per second |
| `DURATION` | `60s` | Measured duration |
| `BENCH_USER_COUNT` | `1` | Number of seeded accounts used for JWTs |
| `PRE_ALLOCATED_VUS` | `10` | Workers k6 prepares initially |
| `MAX_VUS` | `50` | Maximum k6 workers |
| `PAGE_SIZE` | `50` | Messages returned per request |
| `P95_LIMIT_MS` | `500` | p95 threshold |
| `P99_LIMIT_MS` | `1000` | p99 threshold |
| `MAX_ERROR_RATE` | `0.01` | Allowed error fraction (1%) |

For a product-configuration test, keep throttling enabled and use enough distinct
users to avoid measuring one user's rate limit. For a capacity-only test, restart
the API with `BENCHMARK_DISABLE_THROTTLING=true` and label the result accordingly.

## 6. View the reports

Every run writes three ignored files under `benchmarks/results/`:

```text
<timestamp>-api-summary.json   aggregated k6 metrics
<timestamp>-api-samples.csv   individual metric samples
<timestamp>-api-report.html   readable metric cards and explanations
```

Open the HTML report on Linux:

```bash
xdg-open benchmarks/results/<timestamp>-api-report.html
```

The terminal also shows k6's report and the five main values. A nonzero command
exit after a completed run normally means one of the configured latency or error
thresholds failed; the report is still generated.

The CSV is useful for deeper graphs or checking behavior over time. The JSON is the
canonical compact result for comparing repeated runs.

## 7. Find the useful operating limit

Run the same dataset and configuration at progressively higher rates:

```bash
BENCH_PASSWORD='<password>' RATE=10  ROOM_ID=1 BENCH_USER_COUNT=50 ./benchmarks/run_api_benchmark.sh
BENCH_PASSWORD='<password>' RATE=25  ROOM_ID=1 BENCH_USER_COUNT=50 ./benchmarks/run_api_benchmark.sh
BENCH_PASSWORD='<password>' RATE=50  ROOM_ID=1 BENCH_USER_COUNT=50 ./benchmarks/run_api_benchmark.sh
BENCH_PASSWORD='<password>' RATE=100 ROOM_ID=1 BENCH_USER_COUNT=50 ./benchmarks/run_api_benchmark.sh
```

Use a longer `DURATION=5m` for final measurements and repeat each rate at least
three times. The useful limit is the highest achieved rate before latency grows
sharply, errors exceed the threshold, or k6 reports dropped iterations.

Record the Git commit, CPU/RAM, Gunicorn worker count, dataset size, test rate,
duration, throttling mode, and whether the load generator shared the API host.

Do not describe these local results as production capacity. A defensible resume
statement names the environment and workload, for example:

> Benchmarked an authenticated Django message-history API at X requests/sec with
> Y ms p95 latency and Z% errors using four Gunicorn workers and a 10K-row dataset.

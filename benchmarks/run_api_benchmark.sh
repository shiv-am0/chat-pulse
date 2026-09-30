#!/usr/bin/env bash

set -uo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
results_directory="${RESULTS_DIRECTORY:-${repository_root}/benchmarks/results}"
run_id="${RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"
summary_file="${results_directory}/${run_id}-api-summary.json"
samples_file="${results_directory}/${run_id}-api-samples.csv"
report_file="${results_directory}/${run_id}-api-report.html"

if ! command -v k6 >/dev/null 2>&1; then
    echo "k6 was not found. Install k6, then rerun this command." >&2
    exit 127
fi

if [[ -z "${ROOM_ID:-}" ]]; then
    echo "ROOM_ID is required. Use BENCHMARK_ROOM_ID from the seed command." >&2
    exit 2
fi

if [[ -z "${BENCH_PASSWORD:-}" ]]; then
    echo "BENCH_PASSWORD is required and must match BENCHMARK_USER_PASSWORD used while seeding." >&2
    exit 2
fi

mkdir -p "${results_directory}"

k6_environment=(
    -e "ROOM_ID=${ROOM_ID}"
    -e "BENCH_PASSWORD=${BENCH_PASSWORD}"
)
for variable_name in \
    API_URL \
    BENCH_USERNAME_PREFIX \
    BENCH_USER_COUNT \
    RATE \
    DURATION \
    PRE_ALLOCATED_VUS \
    MAX_VUS \
    PAGE_SIZE \
    P95_LIMIT_MS \
    P99_LIMIT_MS \
    MAX_ERROR_RATE
do
    if [[ -n "${!variable_name:-}" ]]; then
        k6_environment+=(-e "${variable_name}=${!variable_name}")
    fi
done

set +e
k6 run \
    "${k6_environment[@]}" \
    --summary-export "${summary_file}" \
    --out "csv=${samples_file}" \
    "${repository_root}/benchmarks/api/history.js"
k6_status=$?
set -e

if [[ -f "${summary_file}" ]]; then
    python3 "${repository_root}/benchmarks/api/render_report.py" \
        "${summary_file}" \
        --output "${report_file}" \
        --duration "${DURATION:-60s}"
    echo "Raw samples: ${samples_file}"
else
    echo "k6 did not create a summary file; no HTML report was generated." >&2
fi

exit "${k6_status}"

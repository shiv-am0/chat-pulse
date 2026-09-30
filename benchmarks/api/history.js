import http from "k6/http";
import exec from "k6/execution";
import { check } from "k6";
import { Counter, Rate, Trend } from "k6/metrics";

const apiUrl = __ENV.API_URL || "http://localhost:8000/api";
const roomId = requiredEnvironmentVariable("ROOM_ID");
const usernamePrefix = __ENV.BENCH_USERNAME_PREFIX || "bench_user_";
const password = requiredEnvironmentVariable("BENCH_PASSWORD");

const targetRate = positiveInteger("RATE", 20);
const preAllocatedVUs = positiveInteger("PRE_ALLOCATED_VUS", 10);
const maxVUs = positiveInteger("MAX_VUS", 50);
const userCount = positiveInteger("BENCH_USER_COUNT", 1);
const pageSize = positiveInteger("PAGE_SIZE", 50);
const p95LimitMs = positiveNumber("P95_LIMIT_MS", 500);
const p99LimitMs = positiveNumber("P99_LIMIT_MS", 1000);
const maximumErrorRate = errorRate("MAX_ERROR_RATE", 0.01);

if (preAllocatedVUs > maxVUs) {
  throw new Error("PRE_ALLOCATED_VUS cannot be greater than MAX_VUS.");
}

export const apiHistoryRequests = new Counter("api_history_requests");
export const apiHistoryErrors = new Rate("api_history_error_rate");
export const apiHistoryLatency = new Trend("api_history_latency", true);

export const options = {
  discardResponseBodies: false,
  setupTimeout: "2m",
  summaryTrendStats: ["avg", "min", "med", "p(90)", "p(95)", "p(99)", "max"],
  scenarios: {
    message_history: {
      executor: "constant-arrival-rate",
      rate: targetRate,
      timeUnit: "1s",
      duration: __ENV.DURATION || "60s",
      preAllocatedVUs,
      maxVUs,
      gracefulStop: "10s",
    },
  },
  thresholds: {
    api_history_error_rate: [`rate<${maximumErrorRate}`],
    api_history_latency: [
      `p(95)<${p95LimitMs}`,
      `p(99)<${p99LimitMs}`,
    ],
    dropped_iterations: ["count==0"],
  },
};

export function setup() {
  const tokens = [];

  for (let index = 1; index <= userCount; index += 1) {
    const username = `${usernamePrefix}${String(index).padStart(4, "0")}`;
    const response = http.post(
      `${apiUrl}/auth/login/`,
      JSON.stringify({ username, password }),
      {
        headers: { "Content-Type": "application/json" },
        tags: { name: "benchmark setup login" },
      },
    );

    let accessToken = null;
    try {
      accessToken = response.json("access");
    } catch (_error) {
      accessToken = null;
    }

    if (response.status !== 200 || !accessToken) {
      throw new Error(
        `Login failed for ${username}: HTTP ${response.status}. ` +
          "Check the seed command output and benchmark credentials.",
      );
    }
    tokens.push(accessToken);
  }

  return { tokens };
}

export default function (data) {
  const tokenIndex = (exec.vu.idInTest - 1) % data.tokens.length;
  const response = http.get(
    `${apiUrl}/messages/?room_id=${roomId}&limit=${pageSize}`,
    {
      headers: { Authorization: `Bearer ${data.tokens[tokenIndex]}` },
      tags: { name: "GET /api/messages/" },
    },
  );

  let responseBody = null;
  try {
    responseBody = response.json();
  } catch (_error) {
    responseBody = null;
  }

  const validResponse =
    response.status === 200 &&
    responseBody !== null &&
    Array.isArray(responseBody.messages);

  check(response, {
    "history status is 200": () => response.status === 200,
    "history response contains messages": () =>
      responseBody !== null && Array.isArray(responseBody.messages),
  });

  // These custom metrics contain only the endpoint under test. Login/setup
  // traffic is intentionally excluded from the reported API benchmark.
  apiHistoryRequests.add(1);
  apiHistoryErrors.add(!validResponse);
  apiHistoryLatency.add(response.timings.duration);
}

function requiredEnvironmentVariable(name) {
  const value = __ENV[name];
  if (!value) {
    throw new Error(`${name} is required.`);
  }
  return value;
}

function positiveInteger(name, fallback) {
  const value = Number(__ENV[name] || fallback);
  if (!Number.isInteger(value) || value < 1) {
    throw new Error(`${name} must be a positive integer.`);
  }
  return value;
}

function positiveNumber(name, fallback) {
  const value = Number(__ENV[name] || fallback);
  if (!Number.isFinite(value) || value <= 0) {
    throw new Error(`${name} must be a positive number.`);
  }
  return value;
}

function errorRate(name, fallback) {
  const value = Number(__ENV[name] ?? fallback);
  if (!Number.isFinite(value) || value <= 0 || value > 1) {
    throw new Error(`${name} must be greater than 0 and no greater than 1.`);
  }
  return value;
}

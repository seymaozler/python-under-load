
import http from "k6/http";
import { check } from "k6";

export const options = {
  scenarios: {
    concurrency_test: {
      executor: "per-vu-iterations",
      vus: 50,
      iterations: 1,
      maxDuration: "30s",
    },
  },
};

export default function () {
  const endpoint = __ENV.ENDPOINT;

  const response = http.get(
    `http://127.0.0.1:8000/experiment/${endpoint}`
  );

  check(response, {
    "status is 200": (r) => r.status === 200,
  });
}

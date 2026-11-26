
import http from "k6/http";
import { check } from "k6";

export const options = {
  scenarios: {
    ten_requests: {
      executor: "per-vu-iterations",
      vus: 10,
      iterations: 1,
      maxDuration: "30s",
    },
  },
};

export default function () {
  const response = http.get(
    "http://127.0.0.1:8000/experiment/db-hold"
  );

  check(response, {
    "status is 200": (r) => r.status === 200,
  });
}

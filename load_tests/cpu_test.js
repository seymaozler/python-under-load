
import http from "k6/http";
import { check } from "k6";

export const options = {
  scenarios: {
    cpu_test: {
      executor: "per-vu-iterations",
      vus: 10,
      iterations: 1,
      maxDuration: "60s",
    },
  },
};

export default function () {
  const endpoint = __ENV.ENDPOINT || "cpu-sync";

  const response = http.get(
    `http://127.0.0.1:8000/experiment/${endpoint}`
  );

  check(response, {
    "status is 200": (r) => r.status === 200,
  });
}

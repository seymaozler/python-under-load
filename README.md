# Python Under Load: Finding the Real Bottlenecks

**Why doesn't more concurrency always mean better performance?**

A hands-on performance lab built with **Python 3.12**, **FastAPI**, **Grafana k6**, and **PostgreSQL**.

The goal is not to compare Python frameworks. It is to understand **why a backend slows down under load**, which resources can become bottlenecks, and how to investigate the cause.

## Research questions

| Area | What I wanted to find out |
| --- | --- |
| Async vs. blocking I/O | What happens when blocking code runs in an async endpoint? |
| Thread pool saturation | How does the AnyIO thread limiter affect synchronous endpoints? |
| CPU-bound workloads | Why doesn't async make CPU calculations parallel? Can more workers help? |
| Database connection pools | Can an async endpoint still slow down while waiting for a database connection? |
| Concurrency limits | Can limiting concurrency improve reliability even if latency increases? |
| Profiling & observability | How can asyncio debug logs and cProfile help identify bottlenecks? |

## Key findings

These are **observed results from short, local k6 tests**, not estimates of production throughput.

| Experiment | Configuration | Result |
| --- | --- | --- |
| Async vs. sync I/O | 100 concurrent requests; simulated 1-second I/O | Avg latency: **1.00s async** vs. **1.86s sync** (first recorded runs) |
| Thread limiter | 100 sync requests; 40 vs. 20 limiter tokens | Avg latency: **1.86s → 3.04s**; p95: **3.07s → 5.06s** |
| CPU worker scaling | 10 CPU-heavy requests; 1 vs. 4 Uvicorn workers | Total test duration: **4.99s → 1.61s** |
| Database pool | 10 requests using PostgreSQL `pg_sleep(1)`; pool 5 vs. 10 | Total test duration: **2.05s → 1.04s** |
| Concurrency limits | 50 requests; simulated downstream limit of 10 operations | Unbounded: **10/50** succeeded; bounded: **50/50** succeeded |

**A useful warning about averages:** The unbounded endpoint had only **204ms average latency**, but **80% of requests failed with HTTP 503**. The bounded endpoint completed all 50 requests, with an average latency of **3.01s**.

Raw k6 summaries are available in [`results/`](results/).

## Stack

- Python 3.12, FastAPI, Uvicorn, AnyIO
- SQLAlchemy (async) and asyncpg
- PostgreSQL 16 (Docker Compose)
- Grafana k6 for load tests
- asyncio debug mode and cProfile
- [uv](https://docs.astral.sh/uv/) for dependencies

## Repository layout

```text
app/
  main.py                # FastAPI app, router registration, AnyIO limiter
  routes/
    io.py                # Async I/O, blocking I/O, sync I/O
    cpu.py               # CPU-intensive Python loop
    database.py          # SQLAlchemy async pool and PostgreSQL wait
    concurrency.py       # Bounded/unbounded downstream simulation
load_tests/              # k6 scenarios
results/
  experiment_01/         # I/O and thread limiter
  experiment_02/         # CPU and worker scaling
  experiment_03/         # Database pools
  experiment_04/         # Concurrency limits
  experiment_06/         # Profiling-related test results
compose.yml
pyproject.toml
uv.lock
```

## Get started

### Prerequisites

Install **Python 3.12**, **uv**, **Docker + Docker Compose**, and **k6**.

### 1. Clone and install

```bash
git clone https://github.com/seymaozler/python-under-load.git
cd python-under-load
uv sync
```

### 2. Start PostgreSQL

```bash
docker compose up -d
docker compose ps
```

The Compose file binds PostgreSQL to **127.0.0.1:5434**. Its `bench` credentials are for this local test database only, **not** for production.

### 3. Set the database URL and start FastAPI

```bash
export DATABASE_URL="postgresql+asyncpg://bench:bench@127.0.0.1:5434/bench"
uv run uvicorn app.main:app --workers 1
```

**Important:** `DATABASE_URL` must be set **before** starting Uvicorn, even when calling non-database endpoints. The database engine is created when its module is imported.

Check [the interactive API docs](http://127.0.0.1:8000/docs) or test:

```bash
curl http://127.0.0.1:8000/health
```

### 4. Run load tests

Keep the API running and open a second terminal in the project directory.

**100 requests: async vs. sync I/O**

```bash
k6 run load_tests/hundred_async.js
k6 run load_tests/hundred_concurrent.js
```

These scripts target `/experiment/async-io` and `/experiment/sync-io` respectively.

**CPU-bound workload:**

```bash
k6 run -e ENDPOINT=cpu-async load_tests/cpu_test.js
```

To compare **1 vs. 4 worker processes**, stop Uvicorn and restart it with `--workers 4`, then run the **same** k6 test again. Keep `DATABASE_URL` set.

**Database connection pool:**

```bash
k6 run load_tests/database_test.js
```

The repository currently uses `pool_size=10` in [`app/routes/database.py`](app/routes/database.py). To reproduce the pool-size-5 run, change it to `5` and **restart** Uvicorn before re-running the same test.

**Concurrency limiting:**

```bash
k6 run -e ENDPOINT=downstream-unbounded load_tests/concurrency_test.js
k6 run -e ENDPOINT=downstream-bounded load_tests/concurrency_test.js
```

HTTP 503 responses are **expected** in the unbounded case because the simulated downstream rejects work beyond 10 concurrent operations.

**Thread limiter:** Change `limiter.total_tokens` from `40` to `20` in [`app/main.py`](app/main.py), restart the one-worker server, and run `load_tests/hundred_concurrent.js` again. Restore `40` after the experiment. This is a limiter for thread-offloaded work, not a global HTTP request limit.

## Profiling

To enable **asyncio debug mode**, restart the server using:

```bash
PYTHONASYNCIODEBUG=1 uv run uvicorn app.main:app --workers 1
```

Make sure `DATABASE_URL` is already set. Then run:

```bash
k6 run -e ENDPOINT=blocking-io load_tests/cpu_test.js
k6 run -e ENDPOINT=cpu-async load_tests/cpu_test.js
```

Watch the Uvicorn terminal for messages such as `Executing <Task ...> took 1.005 seconds`. They describe long event-loop task steps, **not** the total HTTP response time.

To profile the CPU function directly with **cProfile**:

```bash
uv run python -c "import cProfile; from app.routes.cpu import cpu_work; cProfile.run('cpu_work(15_000_000)', 'cpu.prof')"
uv run python -c "import pstats; pstats.Stats('cpu.prof').sort_stats('cumulative').print_stats(12)"
```

In the recorded run, `cpu_work()` took about **0.517 seconds**.

## Methodology and limitations

- k6 scenarios use the `per-vu-iterations` executor, with **one request per virtual user**. These are short bursts, not long-running load or stress tests.
- The API and the load generator ran on the **same local machine**.
- `asyncio.sleep()` and `time.sleep()` are controlled I/O-wait simulations, not real network or disk activity.
- The database benchmark uses real PostgreSQL, but deliberately waits with `pg_sleep(1)`.
- The `asyncio.Semaphore(10)` protects operations **inside one process**. It does not add a bounded waiting queue or coordinate several worker processes.
- Most configurations have one recorded run. The 100-request async/sync tests also have repeated samples.
- Bigger worker counts and pool sizes can consume more resources and are not universal optimizations.

**Main takeaway:** Performance work starts with finding the **actual bottleneck**, not automatically adding workers, threads, or connections. Latency, error rate, and the type of workload should be considered together.

## Article

A longer explanation of these experiments is being prepared for Medium.

---

*This is a learning and performance research project. The numbers reflect the specific test conditions and should not be treated as general FastAPI performance claims.*

# eARA Loops for Software Engineering

> **Note:** This document predates the eARA v1.0 schema. The inline YAML
> snippets below use a pre-v1.0 notation for readability. For valid
> `eara.yaml` configurations, see the `examples/` directory. For the
> formal schema, see `spec/eara.schema.yaml`.

## The gap in the RAMSpeed session

The RAMSpeed session used eARA's discipline -- subagent verification, pre-checks,
keep/discard, results logging -- but it did not use the loop. This was correct for
that task: we had 7 specified improvements, not a search problem. But the loop is
eARA's differentiating feature, and it has clear applications in software
engineering.

This document describes concrete loop scenarios where an agent should run the full
eARA experiment cycle autonomously.

## What makes a task a loop candidate

Three conditions:
1. There is a **measurable metric** that can be checked automatically after each change
2. The **changes are unknown** -- the agent must discover what works through experimentation
3. The agent can make **small, reversible changes** and measure their effect

If all three are true, the full eARA loop applies. If the changes are known (a spec
exists), use eARA discipline without the loop.

## Example 1: API Latency Optimization

```yaml
# eara.yaml
train_script: "src/api/handlers.go"
metric: "p95_latency_ms"
metric_direction: "lower"
compute: "local"
local:
  command: "go test -bench=BenchmarkHandlers -benchtime=10s ./src/api/ | parse_bench.sh"
  results_file: "bench_results.json"
gates:
  tests_pass: "go test ./... exits 0"
  throughput_stable: "rps >= 0.95 * baseline_rps"
  no_goroutine_leaks: "goroutine count stable over 60s"
time_budget_minutes: 5
```

**The loop:**

The agent reads the current p95 latency (say, 120ms). It profiles the handlers,
identifies that JSON serialization dominates. It tries switching to a streaming
encoder. Measures: 95ms. Keep. It tries connection pooling for the database client.
Measures: 80ms. Keep. It tries precomputing a frequently-accessed struct. Measures:
82ms (worse than 80ms after the previous improvement). Discard. It tries reducing
allocations in the hot path. Measures: 65ms. Keep.

Each iteration: modify one thing, benchmark, keep or revert. The agent never asks.
It never stops. It discovers optimizations through experimentation.

**Why this is a loop, not a spec task:** Nobody wrote "switch to streaming JSON
encoder" in a spec. The agent discovered it by profiling and experimenting. The
search space is all possible optimizations to the handler code.

## Example 2: Binary Size Reduction

```yaml
train_script: "go.mod"  # or Cargo.toml, or package.json
metric: "binary_size_bytes"
metric_direction: "lower"
compute: "local"
local:
  command: "go build -o /tmp/app ./cmd/server && stat -f%z /tmp/app"
  results_file: "size_results.json"
gates:
  tests_pass: "go test ./..."
  integration_pass: "make integration-test"
  startup_time: "time /tmp/app --health-check < 2s"
```

**The loop:**

The agent builds the binary (say, 45MB). It analyzes dependencies with `go tool nm`.
It removes an unused logging library. Measures: 42MB. Keep. It replaces a heavy HTTP
router with a lighter one. Measures: 38MB. Keep. It tries removing a debug symbol
table. Measures: 35MB. Keep. It tries replacing encoding/json with a code-generated
alternative. Measures: 36MB (increased). Discard. It tries removing an embedded
asset. Measures: 31MB. Keep.

The gate "integration_pass" prevents the agent from breaking functionality in
pursuit of size. This is the eARA gate concept applied directly.

## Example 3: Test Coverage Improvement

```yaml
train_script: "tests/"  # the agent writes new test files
metric: "coverage_percent"
metric_direction: "higher"
compute: "local"
local:
  command: "pytest --cov=src --cov-report=json && cat coverage.json"
  results_file: "coverage.json"
gates:
  tests_pass: "pytest exits 0"
  no_flaky: "pytest --count=3 exits 0 on all runs"
  meaningful: "new tests cover previously-uncovered branches (not just lines)"
```

**The loop:**

The agent reads current coverage (say, 68%). It identifies uncovered functions in
the auth module. It writes tests for the token refresh flow. Measures: 72%. Keep.
It writes tests for the rate limiter edge cases. Measures: 74%. Keep. It writes
a test that just calls a function without asserting anything meaningful. Measures:
75% but the "meaningful" gate fails (no new branch coverage). Discard. It writes a
test that exercises the error handling path in the rate limiter. Measures: 76%. Keep.

The "meaningful" gate is critical. Without it, the agent would write trivial tests
that inflate coverage without testing real behavior. This is analogous to eARA's ML
gates that prevent optimizing the primary metric at the expense of other properties.

## Example 4: Memory Leak Hunting

```yaml
train_script: "src/server.py"
metric: "rss_growth_mb_per_hour"
metric_direction: "lower"
compute: "local"
local:
  command: "python load_test.py --duration=300 && cat memory_profile.json"
  results_file: "memory_profile.json"
gates:
  tests_pass: "pytest"
  functionality: "curl localhost:8080/health returns 200"
  peak_rss: "peak RSS < 512MB during load test"
time_budget_minutes: 10
```

**The loop:**

The agent runs the load test and measures RSS growth (say, 15MB/hour). It profiles
with tracemalloc, identifies a cache that never evicts. It adds an LRU eviction
policy. Measures: 8MB/hour. Keep. It identifies a connection pool that holds
references to closed connections. It fixes the cleanup logic. Measures: 3MB/hour.
Keep. It tries aggressively garbage-collecting after each request. Measures:
4MB/hour (worse, and adds latency). Discard.

## The universal loop structure

All four examples follow the same structure:

```
LOOP:
  1. Read current state (metric value, gate status)
  2. Analyze: what is the biggest contributor to the metric?
  3. Hypothesize: what change would improve it?
  4. Implement the change (modify source files)
  5. Pre-checks: build, lint, type-check
  6. Measure: run the metric collection command
  7. Check gates: do all constraints still hold?
  8. If metric improved AND gates pass: keep (commit)
  9. If metric worse OR gates fail: discard (git reset)
  10. Log to results.tsv
  11. Post-analysis: why did it work/fail? What to try next?
  12. GOTO 1
```

This is eARA's ML loop with zero structural changes. The only differences are:
- "training" becomes "building and running the metric command"
- "val_loss" becomes "p95_latency" or "binary_size" or "coverage_percent"
- "the training script" becomes "the source files under optimization"

## What stays constant across ALL eARA loops

Regardless of domain (ML, latency, size, coverage, memory):

1. **One metric to optimize.** Not two. Not "latency and also make the code
   prettier." One.
2. **Gates for everything else.** Tests pass. Functionality preserved. No
   regressions. These are non-negotiable constraints, not optimization targets.
3. **Subagent verification before every keep.** The implementing agent does not
   review its own work.
4. **Never stop.** The agent runs until interrupted. If it runs out of ideas, it
   re-reads the code, re-analyzes the profiling data, combines previous near-misses,
   or tries radical changes.
5. **Simple over complex.** A small improvement that adds ugly complexity is not
   worth it. Removing something and getting equal results is a win.
6. **Never push broken code.** Pre-checks are mandatory. If the build fails, fix
   it before measuring.
7. **Log everything.** Every experiment, including failures and discards, goes into
   results.tsv.

## When NOT to loop

- **"Implement feature X per this spec"** -- Execute, don't search. Use eARA
  discipline without the loop.
- **"Fix bug #1234"** -- Diagnose, then fix. Not a search problem.
- **"Refactor module Y to use pattern Z"** -- Known transformation. Execute it.
- **"Add endpoint /api/v2/users"** -- Specified work. Not experimental.

The loop is for **open-ended optimization** where the agent must discover what
works. If a human already knows what to build, write a spec and execute it with
eARA's discipline (pre-checks, subagent verification, keep/discard). Don't force
a loop where there is no search space.

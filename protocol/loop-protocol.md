# eARA Loop Protocol

## Purpose

This document defines the loop state machine for tasks requiring agent
longevity and autonomous operation. The loop is for automation tasks where
the agent must run for extended periods — hours, days, or indefinitely —
experimenting, measuring, and deciding without human intervention.

**The loop is NOT for short optimization bursts.** If the task can be
completed in a few quick iterations, use execution mode with eARA discipline.

---

## When to Use the Loop

The loop applies when ALL three conditions are true:

1. **Longevity or automation**: The task requires the agent to persist
   autonomously for an extended period.
2. **Measurable metric**: There is a quantifiable outcome that can be
   checked automatically after each experiment.
3. **Unknown changes**: The agent must discover what works through
   experimentation, not execute a known specification.

### Canonical loop tasks

- **ML training**: Modify hyperparameters, architecture, data pipeline.
  Measure loss/accuracy. Run for hours or days.
- **System monitoring + auto-remediation**: Watch health metrics. When
  anomalies appear, diagnose, apply fix, verify, continue watching.
- **Long-running test campaigns**: Generate tests, measure coverage,
  keep meaningful ones, discard trivial ones. Run until target coverage.
- **Data pipeline optimization**: Adjust processing parameters, measure
  throughput, keep improvements. Run overnight.
- **Infrastructure tuning**: Adjust configs (cache sizes, pool sizes,
  timeouts), measure performance under load, keep/discard.

### NOT loop tasks

- "Implement this feature per spec" → execution
- "Fix this specific bug" → execution
- "Refactor X to use pattern Y" → execution
- "Make this 20% faster" (one-shot) → execution with eARA discipline

---

## State Machine

```
┌──────┐
│ INIT │
└──┬───┘
   │
   ▼
┌─────────┐
│ ANALYZE │◄──────────────────────────────────┐
└──┬──────┘                                   │
   │                                          │
   ▼                                          │
┌─────────────┐                               │
│ HYPOTHESIZE │                               │
└──┬──────────┘                               │
   │                                          │
   ▼                                          │
┌───────────┐                                 │
│ IMPLEMENT │                                 │
└──┬────────┘                                 │
   │                                          │
   ▼                                          │
┌───────────┐     ┌─────────┐                 │
│ PRE_CHECK │────►│ DISCARD │──┐              │
└──┬────────┘fail └─────────┘  │              │
   │pass                       │              │
   ▼                           │              │
┌─────────┐                    │              │
│ MEASURE │                    │              │
└──┬──────┘                    │              │
   │                           │              │
   ▼                           │              │
┌────────────┐  ┌─────────┐   │              │
│ GATE_CHECK │─►│ DISCARD │──┐│              │
└──┬─────────┘  └─────────┘  ││              │
   │pass               fail  ││              │
   ▼                          ││              │
┌────────┐                    ││              │
│ DECIDE │                    ││              │
└──┬──┬──┘                    ││              │
   │  │                       ││              │
   │  └──worse──►┌─────────┐ ││              │
   │             │ DISCARD │─┘│              │
   │             └─────────┘  │              │
   │improved                  │              │
   ▼                          │              │
┌──────┐                      │              │
│ KEEP │                      │              │
└──┬───┘                      │              │
   │                          │              │
   ▼                          ▼              │
┌───────────────┐   ┌──────────────────┐     │
│ POST_ANALYSIS │◄──│      LOG         │     │
└──┬────────────┘   └──────────────────┘     │
   │                                          │
   ▼                                          │
┌──────────────────┐                          │
│ TERMINATE_CHECK  │                          │
└──┬────────┬──────┘                          │
   │        │                                 │
   │done    │continue                         │
   ▼        └─────────────────────────────────┘
┌──────┐
│ DONE │
└──────┘
```

---

## State Definitions

### INIT

1. Read the resolved eARA config (from bootstrap).
2. Run `metric.collect_command` to establish the baseline value.
3. Set `iteration = 0`, `start_time = now()`.
4. Check for `.eara-state.json`:
   - If it exists, this is a **resume**. Load iteration count, last metric
     value, last commit hash, and hypothesis history.
   - If not, this is a fresh start.
5. Verify all required gates pass. If any fail, HALT — the project must
   be clean before the loop begins.

### ANALYZE

1. Read the current source files. **Actual content, not cached.** If this
   is iteration > 0, the files may have changed since last read.
2. Read the metric collection output.
3. Identify the biggest contributor to the current metric value.
   - For latency: profile to find the hottest path.
   - For loss: analyze which data/architecture choices dominate.
   - For binary size: analyze which dependencies/symbols are largest.
   - For coverage: identify the least-covered modules.
4. Consider the history of previous experiments (what worked, what didn't).

### HYPOTHESIZE

1. Formulate a specific, testable hypothesis:
   > "Changing X in file Y will improve metric by approximately Z because..."
2. The hypothesis MUST be:
   - **Specific**: identifies the exact change.
   - **Testable**: can be verified by measurement.
   - **Falsifiable**: a clear "improved" or "not improved" outcome.
   - **Small**: one change per experiment. Not a bundle of changes.
3. If the agent has run out of hypotheses:
   - Re-read the source code from scratch.
   - Re-analyze profiling/measurement data.
   - Combine insights from previous near-misses.
   - Try radical changes (different algorithm, different data structure).
   - **Never stop.** The loop continues until termination conditions are met.

### IMPLEMENT

1. Make the change to the source files.
2. The change must be:
   - **Small**: one logical change per experiment.
   - **Reversible**: `git reset --hard` undoes it completely.
   - **Isolated**: does not depend on uncommitted changes from prior iterations.

### PRE_CHECK

Run all required gates in order (see `gate-protocol.md` for full details):

1. Run all required gates in order:
   a. `gates.build.command` — must exit 0.
   b. `gates.test.command` — must exit 0 (if required).
   c. `gates.lint.command` — must exit 0 (if required).
   d. Custom gates — in order.
2. If any required gate fails:
   - If `loop.behavior.pause_on_gate_failure` is true: save state, PAUSE,
     wait for user.
   - Otherwise: proceed to DISCARD.

### MEASURE

1. Record `metric_before` (the last known good value).
2. Run `metric.collect_command`.
3. Parse the output as `metric_after`.
4. If the command fails (non-zero exit, unparseable output): treat as
   gate failure.

### GATE_CHECK

1. Run all required gates again (some may depend on the measured state).
2. If any required gate fails: proceed to DISCARD.

### DECIDE

Compare `metric_before` and `metric_after` using `metric.direction`:

- `direction: lower` → keep if `metric_after < metric_before`.
- `direction: higher` → keep if `metric_after > metric_before`.
- `direction: pass` → keep if all gates pass (metric is the composite gate).

Equal values (no improvement) → DISCARD. The loop seeks improvement, not
stasis. If the change has no measurable effect, revert it and try something
different.

### KEEP

1. If the review policy requires review at this strictness level:
   - Dispatch reviewer subagents per `review-protocol.md`.
   - If any required reviewer rejects: proceed to DISCARD instead.
2. If `loop.behavior.auto_commit_on_keep` is true:
   - Commit with a descriptive message including the experiment ID and
     metric improvement.
3. Update the "last known good" metric value.
4. Update the "last known good" commit hash.

### DISCARD

1. If `loop.behavior.auto_revert_on_discard` is true:
   - `git reset --hard {last_good_commit}`.
2. Record why the experiment failed (gate failure, metric regression, or
   reviewer rejection).

### LOG

See `logging-protocol.md` for full logging details.

Append an entry to `logging.results_file` (see `spec/results-schema.yaml`):

```
{timestamp}\t{experiment_id}\tloop_iteration\t{status}\t{metric_before}\t{metric_after}\t{gates_status}\t{commit_hash}\t{description}\t{review_findings}\t{duration_seconds}
```

This happens for BOTH keep and discard. Every experiment is logged.
Failed experiments are as informative as successful ones.

### POST_ANALYSIS

1. **Why did it work/fail?** Record the reasoning.
2. **What does this suggest for the next iteration?** Update the mental
   model of the codebase/system.
3. **Are there patterns in recent results?** If the last 3 experiments all
   failed on the same gate, the approach may be fundamentally wrong.
4. Increment `iteration`.

### TERMINATE_CHECK

Check termination conditions (OR logic — first to trigger wins):

1. `loop.termination.metric_target` — has the metric reached the target?
2. `loop.termination.max_iterations` — has the iteration count been reached?
3. `loop.termination.time_budget_minutes` — has the wall-clock budget expired?

If `loop.behavior.never_stop` is true, **ignore all termination conditions**.
The agent runs until externally interrupted. This is the canonical mode for
ML training and long-running monitoring.

If no termination condition is met: return to ANALYZE.
If any termination condition is met: proceed to DONE.

### DONE

1. Write final state to `.eara-state.json`:
   ```json
   {
     "iteration": 42,
     "last_metric": 0.023,
     "last_commit": "a1b3bee",
     "start_time": "2026-03-24T14:00:00Z",
     "end_time": "2026-03-24T18:32:00Z",
     "total_kept": 15,
     "total_discarded": 27,
     "hypothesis_history": ["...", "..."]
   }
   ```
2. Generate a summary for the user:
   - Total iterations, kept, discarded.
   - Metric improvement (baseline → final).
   - Best single experiment (largest improvement).
   - Time spent.
3. Log the final entry to results.tsv.

### PAUSED (special state)

When `pause_on_gate_failure` is true and a gate fails:

1. Save full state to `.eara-state.json` including:
   - Current experiment (what was attempted).
   - Which gate failed and why.
   - The diff of uncommitted changes.
2. Wait for user input.
3. On resume: return to ANALYZE (the failed experiment has been discarded).

---

## Invariants

These hold at ALL times during the loop, regardless of strictness:

1. **One metric.** Not two. Not "latency and also make the code prettier."
2. **Gates for everything else.** Tests pass. Functionality preserved. No
   regressions. These are constraints, not optimization targets.
3. **Never stop within the loop.** If the agent runs out of ideas, it
   re-reads, re-analyzes, combines previous near-misses, or tries radical
   changes. It does not ask. It does not pause (unless `pause_on_gate_failure`).
4. **Simple over complex.** A small improvement that adds ugly complexity is
   questionable. Removing something and getting equal results is a win.
5. **Never push broken code.** Pre-checks are mandatory. If the build fails,
   fix it before measuring.
6. **Log everything.** Every experiment — including failures — is logged.
7. **Subagent verification before every keep** (at standard+). The
   implementing logic does not review its own output.
8. **Framing gates override the loop.** If a framing correction triggers
   `halt_and_audit`, the loop pauses regardless of `never_stop`. Fix all
   framing instances, verify, then resume. Framing contamination invalidates
   everything built on wrong assumptions — the loop cannot produce valid
   results if the agent misunderstands what it is building.
9. **Persistent gate failure escalation.** If the same gate fails on 5+
   consecutive iterations, the loop enters PAUSED regardless of
   `pause_on_gate_failure`. Log the failure pattern. The loop cannot make
   progress — the user must intervene.

---

## Context Resets (v2.0)

**When `loop.context_reset.enabled` is true.**

Anthropic found that automatic compaction is insufficient for long sessions.
Claude exhibited "context anxiety" — prematurely concluding work as the
context window filled — that only full context resets resolved. For loops
running hours or days, prescribed context resets prevent degradation.

### When to reset

A reset triggers when ANY of these conditions is met:
- `interval_iterations` iterations have elapsed since last reset.
- `interval_minutes` minutes of wall-clock time have elapsed.
- The agent detects quality degradation (hypotheses becoming repetitive,
  same experiments being tried again, declining metric trajectory).

### Reset procedure

See `context-reset-protocol.md` for the full protocol. Summary:

1. Write current state to `.eara-state.json`.
2. Log a "context_reset" entry to results.tsv.
3. Clear the context window entirely.
4. Reconstruct from persistent state:
   a. Read `.eara-state.json` (iteration count, last metric, last commit).
   b. Read the last 10 entries of results.tsv (recent experiment history).
   c. Read the current source files (fresh, not from memory).
   d. Read the eara.yaml config.
5. Resume the loop from ANALYZE with clean context.

The key insight: everything the agent needs to continue is in files.
The context window is a working scratchpad, not permanent storage.

---

## Collaborative Loop Mode (v2.0)

**When `loop.collaborative.enabled` is true.**

Karpathy envisions "emulating a research community" — multiple agents
exploring different optimization paths in parallel, promoting promising
ideas to larger scales. This mode coordinates multiple parallel loop
instances.

### Architecture

```
              ┌─── Loop Instance A ───┐
              │  source_files (copy A) │
              │  local results log     │──┐
              └────────────────────────┘  │
                                          ▼
              ┌─── Loop Instance B ───┐  shared
              │  source_files (copy B) │  results.tsv
              │  local results log     │──┤
              └────────────────────────┘  │
                                          ▼
              ┌─── Loop Instance C ───┐  cross-
              │  source_files (copy C) │  pollination
              │  local results log     │──┘
              └────────────────────────┘
```

### Coordination rules

1. Each instance operates on its own copy of the source files (separate
   git branches or worktrees).
2. Each instance logs to a local results file AND appends to the shared
   `shared_results_file`.
3. When `cross_pollination` is true, each instance periodically reads the
   shared results to learn from other instances' successes and failures.
4. A successful experiment in one instance can be tested in another by
   cherry-picking the commit and re-measuring.
5. Instances do NOT coordinate in real-time. Coordination is through the
   shared results file only — asynchronous, like a real research community.

### Promotion

When an experiment shows consistent improvement across 2+ instances, it is
promoted: applied to the main branch and incorporated into all instances'
starting state for the next context reset.

---

## Transfer Verification (v2.0)

**When `loop.transfer_verification.enabled` is true.**

Karpathy found that 20 improvements on a small model transferred to larger
models. This gate tests whether discoveries generalize.

### Process

After a KEEP decision (experiment improves the metric and passes all gates):

1. Run `loop.transfer_verification.command` — this should execute the
   improvement in a different context (larger model, production data,
   different hardware).
2. If the improvement holds in the transfer context: log as
   `keep+transferred` in results.tsv.
3. If the improvement does NOT transfer: log as `keep+no_transfer`.
   The experiment is still kept (it improved the primary metric), but
   the transfer failure is recorded for analysis.

This does not block the KEEP decision. Transfer verification is
informational — it identifies which discoveries are robust versus
which are specific to the current scale or context.

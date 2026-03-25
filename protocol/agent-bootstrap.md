# eARA Agent Bootstrap Protocol

## Purpose

This document defines what an agent does when it starts a session in a project
that contains an `eara.yaml` configuration file. The bootstrap is mandatory and
must complete before any implementation work begins.

The bootstrap sequence differs between normal and ultra strictness. Ultra
requires reading the full protocol stack and injecting it into every
dispatched subagent.

---

## Step 1: Detect and Parse

Check the project root for `eara.yaml`. If found:

1. Parse the YAML file.
2. Validate against `spec/eara.schema.yaml`.
3. If validation fails, HALT and report the error to the user. Do not proceed
   with invalid configuration.

If `eara.yaml` is not found, eARA discipline is not active for this project.
The agent may still choose to follow eARA principles voluntarily, but they are
not enforced.

---

## Step 2: Resolve Strictness Profile

1. Read the `strictness` field.
2. If it is a string (`normal` or `ultra`), load the corresponding profile
   from `spec/strictness-profiles.yaml`.
3. If it is an object with `profile` and `overrides`, load the base profile
   and deep-merge the overrides:
   - Scalars and booleans: overrides REPLACE base values.
   - Arrays: overrides APPEND to base arrays.
   - Objects: overrides merge recursively.
4. Store the resolved configuration in working memory. This is the effective
   config for the entire session.

---

## Step 3: Read Protocol Stack (mode-dependent)

### Normal mode bootstrap

Read the following files:

1. `eara.yaml` (already parsed in Step 1)
2. The relevant operational protocol:
   - `protocol/execution-protocol.md` if mode is `execution`
   - `protocol/loop-protocol.md` if mode is `loop`

Reading `spec/program.md` is recommended but not required. The agent operates
with the configuration and the relevant protocol.

### Ultra mode bootstrap

Read ALL of the following files. This is not optional:

1. `eara.yaml` (already parsed in Step 1)
2. `spec/program.md` — the complete behavioral contract
3. `spec/rationalizations.yaml` — the 28 mandatory halt signals
4. The relevant operational protocol:
   - `protocol/execution-protocol.md` if mode is `execution`
   - `protocol/loop-protocol.md` if mode is `loop`
5. `protocol/review-protocol.md` — subagent dispatch rules
6. `protocol/gate-protocol.md` — gate ordering and failure handling

**Why ultra requires the full stack:** Agents skip eARA files when they are
not forced to read them. The normal bootstrap trusts agents to follow the
configuration. Ultra does not trust agents — it forces them to read the
protocol before they can act. This is the defining difference.

**Subagent injection:** At ultra, every dispatched subagent also receives the
full protocol stack in its prompt. Not a summary. Not "follow eARA." The
actual file contents. A subagent that has the rationalizations in its prompt
cannot skip them.

---

## Step 4: Classify the Task

Read the `mode` field:

- **`execution`**: The changes are known. Follow `execution-protocol.md`.
- **`loop`**: The agent runs autonomously for extended periods. Follow `loop-protocol.md`.

If `mode` is not set, classify based on the task description:

| Signal | Classification |
|---|---|
| Task requires running for hours or days | loop |
| Task has a measurable metric + unknown changes to discover | loop |
| Task is "implement X per this spec" | execution |
| Task is "fix bug #N" | execution |
| Task is "make this faster" (short burst) | execution with eARA discipline |
| Task is "continuously optimize and monitor" | loop |
| Task is "train this model" | loop |
| Task is "refactor X to use Y" | execution |

If ambiguous, ask the user. Do not guess.

---

## Step 5: Initialize Gates

Run all required gates to verify the project is in a clean starting state:

1. Run `gates.build.command` — the project must build.
2. Run `gates.test.command` (if required) — all tests must pass.
3. Run `gates.lint.command` (if required) — no lint errors.
4. Run any `gates.custom_gates` that are required.

**If any required gate fails at session start, HALT.** The project must be in
a passing state before eARA begins. Do not attempt to fix pre-existing failures
unless the user explicitly asks.

Record the baseline gate status. This is the "known good" state.

See `gate-protocol.md` for gate checking order and failure handling.

---

## Step 6: Initialize Metric (if applicable)

If `metric` is defined:

1. Run `metric.collect_command` to measure the current value.
2. If `metric.baseline` is null, set it to the measured value.
3. Record the baseline. This is the starting point for improvement.

If `metric` is not defined (execution mode where gates serve as the pass/fail
criterion), the gates themselves are the composite metric.

---

## Step 7: Initialize Logging

See `logging-protocol.md` for full logging details.

If `logging.auto_log` is true:

1. Check if `logging.results_file` exists.
2. If not, create it with the header row (see `spec/results-schema.yaml`).
3. If it exists, read the last entry to determine:
   - Current experiment ID (for incrementing).
   - Last known metric value (for comparison).
   - Session resume state.

---

## Step 8: Load Rationalizations

Load `spec/rationalizations.yaml`. For each rationalization:

1. Check if it applies at the current strictness level (see `applies_at`).
2. Store the applicable rationalizations as active STOP signals.
3. During the session, if the agent's reasoning matches any rationalization's
   `thought` field, the agent must:
   - STOP the current action.
   - Read the `why_wrong` field.
   - Reconsider the approach.
   - This is not optional. Rationalizations are mandatory halt signals.

At **ultra**, the rationalizations were already read in Step 3 as part of
the full protocol stack. This step activates them as pattern-match triggers.

---

## Step 9: Internalize Framing

If `framing` is defined:

1. Store `framing.project_identity` as the canonical description.
2. Store `framing.project_is_not` as banned terms.
3. Activate `framing.correction_protocol`:
   - `note`: Record corrections in memory, continue working.
   - `halt_and_audit`: When the user corrects framing, STOP immediately.
     Search all outputs and files for the old framing. Fix every instance.
     Verify the fix (search should return zero results). Resume only after
     verification.
4. If `framing.verify_framing_on_commit` is true (ultra): before every
   commit, check that no staged content contains terms from `project_is_not`.

---

## Step 10: Load Boundaries (if applicable)

If `boundaries` is defined:

1. Store the project boundary definitions.
2. If `boundaries.scope_gate` is true, activate the scope check:
   before every commit, verify each staged file matches the
   `allowed_file_patterns` and does not match `forbidden_file_patterns`
   for its project.
3. If `boundaries.cross_project_verification` is true (ultra by default),
   also verify that no artifact in the working directory belongs to a
   different project in the boundary list.

---

## Step 11: Begin Work

Bootstrap is complete. Proceed to:

- `execution-protocol.md` if mode is `execution`.
- `loop-protocol.md` if mode is `loop`.

**The bootstrap must complete before any code is written or modified.**

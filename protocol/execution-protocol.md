# eARA Execution Protocol

## Purpose

This document defines the discipline for tasks where the changes are known —
implementing a spec, fixing a bug, refactoring code. No loop. The agent
executes, verifies, and ships. eARA discipline (pre-checks, subagent
verification, keep/discard, logging) is applied to every step.

---

## When to Use Execution Mode

- "Implement these 7 improvements per this spec" → execution
- "Fix bug #1234" → execution
- "Refactor module Y to use pattern Z" → execution
- "Add endpoint /api/v2/users" → execution
- Any task where the changes are specified upfront, not discovered

---

## The Execution Cycle

For each task or logical unit of work:

### 1. DESCRIBE

State what will change and why. This is not optional. Before touching code:

- What file(s) will be modified?
- What is the expected outcome?
- What gates must pass after the change?

Write this into the experiment log if `logging.auto_log` is true.

### 2. DISPATCH

Send the task to an implementation subagent with precisely crafted context:

**Include:**
- Full specification text (not a summary, the actual spec)
- Relevant file contents (current state — read them fresh, do not rely on
  cached reads from earlier in the session)
- Architectural context (what depends on these files, what these files
  depend on)
- Gate requirements (what must pass after implementation)

**Exclude:**
- Session history (the subagent does not need your conversation context)
- Unrelated file contents
- Your assumptions about the code (let the subagent form its own)

Subagent dispatch is mandatory for non-trivial changes at both normal
and ultra. At **ultra**, every dispatched subagent receives the full
eARA protocol stack injected into its prompt.

### 3. PRE-CHECKS

After receiving the implementation, run all required gates in order (see
`gate-protocol.md` for full gate checking order and failure handling):

1. **Build gate**: `gates.build.command` must exit 0.
2. **Test gate**: `gates.test.command` must exit 0 (if required at this
   strictness level).
3. **Lint gate**: `gates.lint.command` must exit 0 (if required).
4. **Custom gates**: in order.

If any required gate fails:
- Fix in-place if the fix is obvious and small.
- If the fix is non-trivial, discard the entire implementation and
  re-dispatch with additional context about the failure.
- **Never "keep with known failures."**

### 4. REVIEW

Based on the resolved review policy, dispatch reviewer subagents. See
`review-protocol.md` for full details.

At **normal**: spec compliance review (code quality via override).
At **ultra**: spec compliance + code quality review + per-file overrides
  (native code, security) + calibration checks + evidence requirements.

Each reviewer receives:
- The actual file content (NOT the implementer's report)
- The spec/requirements
- The instruction: "The implementer's report may be wrong. Verify independently."

### 5. DECIDE

Binary keep/discard:

- All required gates pass AND all required reviewers approve → **KEEP**
- Any required gate fails OR any required reviewer rejects → **DISCARD or FIX**

There is no middle ground. No "keep with known issues." No "keep and fix
later." The experiment either passes completely or it does not count.

### 6. COMMIT

**Before committing, produce BOTH gate records:**

1. **AGENT COUNT GATE** (see `review-protocol.md`, section "Mandatory
   Agent Count Gate"). Lists every required agent type and confirms
   dispatched + returned. BLOCKED if any required agent is MISSING.

2. **REVIEW GATE VERIFICATION** (see `review-protocol.md`, section
   "Commit Gate: Mandatory Review Receipt Verification"). Lists every
   reviewer with agent ID and result. BLOCKED if any required reviewer
   has not returned PASS.

Both records must appear in the conversation BEFORE the commit command.
Both gates must show PASS. If either is BLOCKED, fix and re-verify.

If the record shows BLOCKED: fix issues, re-dispatch failed reviewers,
and produce a new record. Do not commit.

If KEEP and gate decision is COMMIT:
- Commit atomically with a descriptive message.
- One commit per logical unit of work (not bulk commits at the end).
- The commit message should describe what changed and why.

### 7. LOG (see `logging-protocol.md` for full details)

Append to `logging.results_file`:

```
{timestamp}\t{experiment_id}\timplementer\t{status}\t-\t-\t{gates_status}\t{commit_hash}\t{description}\t-\t{duration_seconds}
```

For execution mode, `metric_before` and `metric_after` are typically `-`
(null) unless a specific metric is being tracked.

### 8. POST-MERGE VERIFICATION

If `gates.post_merge_verification.enabled` is true (ultra, or normal with override):

After merging any parallel work (worktrees, branches), before proceeding:

1. Run `gates.build.command` from scratch (clean build, not incremental).
2. Run `gates.test.command` (full suite, not just changed files).
3. Run all other required gates.

If any gate fails after merge:
- Diagnose the failure.
- Fix before proceeding to the next merge or next task.
- Do NOT proceed with a broken main branch.

### 9. REPEAT

Move to the next task. The cycle repeats for each logical unit of work.

---

## Test-Before-Ship Gate

At both **normal** and **ultra**, when `gates.test_before_ship.enabled` is true:

Before marking an experiment as KEEP, check:

1. Does this change introduce new public surface? (new functions, tools,
   endpoints, API methods, public types)
2. If yes: do tests exist that exercise the new surface?
3. If no tests exist: the experiment is **NOT eligible for KEEP**.

The agent must either:
- Write the tests as part of the same experiment.
- Dispatch a subagent to write the tests.

Zero-test commits for new surface are equivalent to untested experiments.
They do not count as "keep" until verified.

---

## Boundary Gate

At **ultra** (or normal with override), when `boundaries.scope_gate` is true:

Before every commit, check each staged file:

1. Does this file match an `allowed_file_patterns` entry for the current
   project?
2. Does this file match a `forbidden_file_patterns` entry?
3. If forbidden or if the file belongs to a different project in the
   boundary list: **BLOCK the commit** and report the violation.

---

## Framing Gate

At both **normal** and **ultra**, when a user corrects a project-level assumption:

1. **HALT** current work immediately.
2. Search all files and outputs for instances of the incorrect framing.
3. Fix every instance.
4. Verify the fix (search should return zero results).
5. Resume only after verification.

At **ultra** (`framing.verify_framing_on_commit`):
- Before every commit, search staged content for terms in `framing.project_is_not`.
- If any banned term is found: block the commit.

---

## What Execution Mode Keeps from eARA

Even without the loop, execution mode preserves all five eARA invariants:

1. **Mandatory subagent verification** (normal and ultra). Fresh context
   prevents blind spots. Independent review prevents optimistic self-assessment.
2. **Pre-run checks** before every experiment. Build, test, lint, custom gates.
3. **Binary keep/discard**. No "keep with known issues."
4. **Append-only results logging** (normal and ultra). Every experiment logged.
5. **Rationalizations table active**. If the agent thinks "this is simple
   enough to skip review," it must STOP.

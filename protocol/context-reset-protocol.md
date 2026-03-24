# eARA Context Reset Protocol (v2.0)

## Purpose

This document defines when and how to perform full context resets during
long-running loops. Based on Anthropic's finding that automatic compaction
is insufficient for sessions spanning hours or days — Claude exhibited
"context anxiety" (prematurely concluding work as context fills) that only
full resets resolved.

The core insight: everything the agent needs to continue is in files. The
context window is a working scratchpad, not permanent storage. A reset
clears the scratchpad and reconstructs from persistent state.

---

## When to Reset

A context reset triggers when ANY of these conditions is met:

1. **Iteration interval**: `loop.context_reset.interval_iterations`
   iterations have elapsed since the last reset.
2. **Time interval**: `loop.context_reset.interval_minutes` minutes of
   wall-clock time have elapsed since the last reset.
3. **Quality degradation** (agent-detected):
   - Hypotheses becoming repetitive (proposing changes already tried).
   - Same experiments being attempted again (check results.tsv).
   - Declining metric trajectory over 5+ consecutive iterations.
   - Agent recognizes its own reasoning is becoming circular.

Condition 3 is a judgment call by the agent. Conditions 1 and 2 are
mechanical triggers. When in doubt, reset. A clean context is always
better than a polluted one.

---

## Pre-Reset Procedure

Before clearing context, persist everything needed for reconstruction:

### 1. Write state file

Write or update `.eara-state.json`:

```json
{
  "eara_version": "2.0",
  "iteration": 42,
  "last_metric": 0.023,
  "best_metric": 0.019,
  "best_commit": "a1b3bee",
  "last_commit": "c3d5e00",
  "start_time": "2026-03-24T14:00:00Z",
  "last_reset_time": "2026-03-24T18:00:00Z",
  "total_kept": 15,
  "total_discarded": 27,
  "recent_hypothesis_themes": [
    "connection pooling",
    "serialization optimization",
    "cache eviction policies"
  ],
  "exhausted_approaches": [
    "goroutine-per-request (OOM at scale)",
    "custom allocator (marginal gain, high complexity)"
  ],
  "current_focus": "database query optimization",
  "context_resets": 3
}
```

### 2. Log the reset

Append to results.tsv:

```
{timestamp}\t{experiment_id}\torchestrator\tcontext_reset\t{metric_before}\t-\tpass\t-\tcontext reset: iteration {N}, {reason}\t-\t0
```

### 3. Commit any uncommitted work

If there are uncommitted changes, either commit them (if they pass gates)
or stash/discard them. The reset must start from a clean git state.

---

## Post-Reset Reconstruction

After clearing the context window, reconstruct working state from files
in this order:

### Step 1: Read configuration

Read `eara.yaml`. Resolve the strictness profile. This re-establishes
the behavioral contract.

### Step 2: Read state

Read `.eara-state.json`. This provides:
- Where you are in the loop (iteration count).
- The current metric value and best metric value.
- What has been tried (exhausted approaches).
- What you were working on (current focus).

### Step 3: Read recent history

Read the last 10-20 entries of `results.tsv`. This provides:
- What was tried recently and whether it worked.
- The metric trajectory (improving, plateauing, or declining).
- Which gates have been failing.

Do NOT read the entire results.tsv — only the recent tail. For loops
running hundreds of iterations, the full history is too large to fit in
context and most of it is not actionable.

### Step 4: Read source files

Read the current source files (the files listed in `source_files` in
eara.yaml). Read the actual file contents, not what you remember from
before the reset.

### Step 5: Read contracts and review files (if applicable)

If contract negotiation or file-based review is enabled, read any active
`.eara-contract.md` and recent review result files.

### Step 6: Resume

Enter the ANALYZE state of the loop protocol. You now have clean context
with all necessary state reconstructed from files.

---

## What to Preserve vs. Discard

| Preserve (in files) | Discard (context only) |
|---|---|
| Iteration count | Intermediate reasoning from prior iterations |
| Metric values (current, best) | Detailed analysis of failed experiments |
| Exhausted approaches | Full file contents from prior reads |
| Current focus area | Conversation history with reviewers |
| Results.tsv entries | Subagent dispatch details |
| Git commit history | Tentative hypotheses that were never tested |
| Sprint contracts | Internal deliberation about what to try |

The principle: **persist decisions, discard deliberation.** The decisions
are in the results log, the git history, and the state file. The
deliberation that led to those decisions does not need to survive the reset.

---

## File-Based Handoff Format

For inter-session handoffs (when the agent framework itself restarts, not
just a context reset within a session), use a structured handoff file:

```markdown
# eARA Loop Handoff

## Status
- Iteration: {N}
- Metric: {current} (best: {best} at commit {hash})
- Mode: {loop, running | loop, paused | done}

## What Worked
- {description of successful experiments, with commit hashes}

## What Failed
- {description of failed approaches and why}

## Next Steps
- {what the next iteration should try}
- {what the current analysis suggests}

## Open Questions
- {unresolved issues that the next session should investigate}
```

This file is written at the end of each session and read at the start of
the next. It bridges the gap between sessions where `.eara-state.json`
provides structured data but lacks narrative context.

---

## Interaction with Collaborative Mode

In collaborative mode, each loop instance performs its own context resets
independently. The shared results file provides cross-instance context
after each reset — the agent reads recent entries from other instances
to learn from their successes and failures without needing to share
context windows.

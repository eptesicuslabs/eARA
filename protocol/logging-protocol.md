# eARA Logging Protocol

## Purpose

Every experiment is logged. Every failure is logged. The append-only results
log creates accountability, traceability, and a structured record that
survives beyond the session. When something breaks later, the log traces
exactly which experiment introduced the change.

---

## Core Principle

> The log is maintained by the framework, not the agent.

When `logging.auto_log` is true (enabled at both normal and ultra), logging
happens automatically after every KEEP or DISCARD decision. The agent does
not need to remember to log. This removes the "I forgot to log" failure
mode that the eMCP session demonstrated.

---

## Format

TSV (Tab-Separated Values). Not CSV, not JSON.

**Why TSV:**
- Append-friendly: just add a line. JSON requires balanced brackets.
- Human-readable: opens cleanly in any text editor or spreadsheet.
- No escaping needed for most content (unlike CSV with commas in descriptions).
- Matches the convention from the RAMSpeed case study.

**Encoding:** UTF-8.
**Line endings:** LF (Unix-style).

---

## Column Layout

See `spec/results-schema.yaml` for the full schema. Summary:

```
timestamp  experiment_id  agent_type  status  metric_before  metric_after  gates_status  commit_hash  description  review_findings  duration_seconds
```

### Column Details

| Column | Type | Example | Notes |
|---|---|---|---|
| timestamp | ISO 8601 datetime | 2026-03-24T14:32:01Z | When the decision was made |
| experiment_id | E + zero-padded number | E001 | Sequential per session |
| agent_type | enum | implementer | See results-schema for full enum |
| status | enum | keep | keep, discard, blocked, error, gate_fail |
| metric_before | number or `-` | 120 | `-` if no metric defined |
| metric_after | number or `-` | 95 | `-` if discarded before measurement |
| gates_status | string | pass | `pass`, `fail:build`, `fail:test`, `skip` |
| commit_hash | 7-char hash or `-` | a1b3bee | `-` if discarded |
| description | string (no tabs) | switched to streaming encoder | What was attempted |
| review_findings | string or `-` | uint/int mismatch in scroll | Only at ultra (log_review_findings) |
| duration_seconds | number | 180 | Wall-clock from start to decision |

---

## When to Log

### Always logged (at normal and ultra):

1. **After KEEP**: experiment passed all gates, committed.
2. **After DISCARD**: experiment failed metric, gates, or review.
3. **After ERROR**: unexpected failure (build crash, timeout, etc.).

### Optionally logged (at ultra, when log_dispatches is true):

4. **Subagent dispatches**: when an implementation subagent is sent.
5. **Review dispatches**: when a reviewer subagent is sent.
6. **Review completions**: when a reviewer returns its verdict.

---

## Initialization

At session start (during bootstrap):

1. Check if `logging.results_file` exists.
2. **If not:** Create it with the header row:
   ```
   timestamp\texperiment_id\tagent_type\tstatus\tmetric_before\tmetric_after\tgates_status\tcommit_hash\tdescription\treview_findings\tduration_seconds
   ```
3. **If exists (resume):** Read the last entry to determine:
   - The current experiment ID (for incrementing).
   - The last known metric value (for comparison).
   - Whether this is a session resume.

---

## Append Rules

1. **Append only.** Never modify existing entries. Never delete entries.
   The log is an immutable record.
2. **One entry per decision.** Each KEEP or DISCARD gets exactly one row.
   Do not batch multiple experiments into one entry.
3. **Log failures, not just successes.** A discarded experiment is as
   informative as a kept one. The log should show what was tried and failed,
   not just what worked.
4. **No tabs in description.** The description field must not contain tab
   characters (they would break TSV parsing). Replace tabs with spaces.
5. **Timestamps are UTC.** Not local time. This ensures logs from different
   machines are comparable.

---

## Example Log

```tsv
timestamp	experiment_id	agent_type	status	metric_before	metric_after	gates_status	commit_hash	description	review_findings	duration_seconds
2026-03-24T14:32:01Z	E001	implementer	keep	-	-	pass	3def8ae	settings: 5 new properties with validation clamping	-	45
2026-03-24T14:35:22Z	E001	spec_reviewer	keep	-	-	pass	-	spec review: settings match spec, no issues	-	12
2026-03-24T14:38:15Z	E001	quality_reviewer	keep	-	-	pass	-	quality review: minor rename suggestion (targetAvailableBytes)	rename suggestion	8
2026-03-24T15:01:00Z	E002	implementer	keep	-	-	pass	a1b3bee	adaptive escalation: OptimizeAll restructured with per-tier early exit	-	120
2026-03-24T15:15:00Z	E003	loop_iteration	keep	120	95	pass	b2c4dff	switched to streaming JSON encoder	-	180
2026-03-24T15:18:30Z	E004	loop_iteration	discard	95	98	fail:test	-	tried connection pool tuning (throughput regressed, test timeout)	-	210
2026-03-24T15:22:00Z	E005	loop_iteration	keep	95	80	pass	c3d5e00	added database connection pooling	-	195
```

---

## Post-Session Analysis

The results log enables:

1. **Session reconstruction**: What was done, in what order, with what outcome.
2. **Efficiency analysis**: What percentage of experiments were kept vs. discarded?
3. **Gate failure patterns**: Which gates fail most often? (indicates systemic issues)
4. **Metric trajectory**: How did the metric improve over iterations? (loop mode)
5. **Time analysis**: How long does each experiment take? Where is time spent?
6. **Review value analysis**: How often do reviewers catch issues that would have
   been shipped without review?

The eMCP session had no results.tsv. Reconstructing the session narrative required
reading git history and relying on memory. With a proper log, every decision would
have been traceable.

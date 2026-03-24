# eARA Review Protocol

## Purpose

Subagent verification is the single highest-value component of eARA. This
document defines how reviewer subagents are dispatched, prompted, and
verified. A single agent accumulates blind spots over a long session. It
becomes anchored to its own assumptions. Fresh reviewers break that anchor.

---

## Core Principle

> The implementing agent does not review its own work. Ever.

This is non-negotiable at standard+ strictness. The implementer's self-report
may be incomplete, inaccurate, or optimistic. Independent verification by a
fresh-context subagent is the primary quality mechanism.

**Empirical evidence:** The eMCP session showed a direct correlation between
review compliance rate and preventable bug rate (60% → 60%). The RAMSpeed
session with 100% review compliance had zero reverts and caught 5 real issues.

---

## Reviewer Types

### Spec Compliance Reviewer

**Purpose:** Verify that the implementation matches the specification line
by line. Not "generally matches" — specifically, concretely matches.

**Dispatched at:** standard, strict, paranoid.

**Default prompt structure:**
```
You are reviewing an implementation for spec compliance.

SPECIFICATION:
{full_spec_text}

IMPLEMENTATION (actual file content):
{file_content}

INSTRUCTIONS:
- Compare the implementation against the specification line by line.
- The implementer finished this work. Their report may be incomplete,
  inaccurate, or optimistic. You MUST verify everything independently.
- Do NOT trust the implementer's self-assessment.
- For every claim you make, reference the specific line numbers in the
  implementation.
- Report: PASS (spec fully met) or FAIL (with specific deviations).
```

### Code Quality Reviewer

**Purpose:** Check naming, duplication, architectural consistency, edge
cases, error handling, and adherence to project conventions.

**Dispatched at:** standard, strict, paranoid.

**Default prompt structure:**
```
You are reviewing code quality for a recent implementation.

IMPLEMENTATION (actual file content):
{file_content}

PROJECT CONVENTIONS:
{relevant_convention_docs_or_examples}

INSTRUCTIONS:
- Check naming consistency with the rest of the codebase.
- Identify duplicated logic that should be extracted.
- Check edge cases: null/undefined handling, boundary values, error paths.
- Verify the code follows project conventions (patterns, naming, structure).
- Report: PASS (no issues) or ISSUES (with specific findings and line numbers).
```

### Native Code Reviewer

**Purpose:** Review code that calls OS APIs, FFI, P/Invoke, native bindings.
This reviewer has specialized knowledge of platform-specific bugs.

**Dispatched at:** strict (per-file override), paranoid (always).

**Triggered by:** Files matching `per_file_overrides` patterns with
`extra_reviewers: [native_code]`.

**Default prompt structure:**
```
You are reviewing native/platform code.

IMPLEMENTATION (actual file content):
{file_content}

INSTRUCTIONS:
- Check sign/unsigned mismatches in function signatures (classic P/Invoke bug).
- Check pointer lifetime and memory management.
- Check platform-specific assumptions (endianness, path separators, API availability).
- Check error code handling (many OS APIs return error codes, not exceptions).
- The eMCP session had a uint/int mismatch in mouse_event that broke
  scroll-down on Windows. This class of bug is your primary target.
- Report: PASS or ISSUES (with specific findings and line numbers).
```

### Security Reviewer

**Purpose:** Review code that touches auth, crypto, permissions, or security
boundaries.

**Dispatched at:** strict (per-file override), paranoid (always).

**Triggered by:** Files matching `per_file_overrides` patterns with
`extra_reviewers: [security]`.

---

## Dispatch Rules

### What to send to reviewers

**ALWAYS include:**
- The actual file content (fresh read, not cached).
- The spec or requirements for this change.
- The adversarial instruction ("do not trust the implementer's report").

**NEVER include:**
- The implementer's self-report as ground truth.
- Session history or context from other tasks.
- Your assumptions about what the code does.

### What NOT to do

- Do NOT ask the implementer to review its own work.
- Do NOT merge the review into the same subagent that implemented the change.
- Do NOT summarize the implementation for the reviewer — let the reviewer
  read the actual code.

---

## Evidence Requirements

At **strict** and **paranoid** strictness, evidence requirements are enforced.

### When `evidence_requirements.require_quotes` is true:

Reviewer responses must include direct quotes from the reviewed files. A claim
like "the function handles null correctly" is insufficient. The reviewer must
quote the specific null-handling code.

### When `evidence_requirements.require_line_numbers` is true:

Every claim must reference specific line numbers. "Line 42 checks for null
before dereferencing" is valid. "The code checks for null" is not.

### When `evidence_requirements.require_file_sizes` is true (paranoid):

For audit/assessment reviews, the reviewer must report file sizes. This
prevents fabrication — an audit that claims a 300-line file is a "stub"
can be cross-checked against the actual file size.

### Enforcement

If a reviewer's response lacks the required evidence:
1. **Reject** the response.
2. **Re-dispatch** with explicit instructions about what evidence is needed.
3. If the re-dispatched review still lacks evidence, escalate to the
   orchestrator for manual verification.

---

## Calibration Checks

At **strict+** strictness, when `review.reviewers.calibration.enabled` is true:

Before trusting an **audit or assessment** subagent's output:

1. Select `calibration.sample_size` items whose ground truth is already known
   (e.g., files you have already read and understand).
2. Run the audit subagent on these known items.
3. Compare the audit's assessment against your known ground truth.
4. If the audit disagrees with ground truth on ANY item:
   - **Discard the entire audit.**
   - Re-dispatch with stricter prompting:
     - Require direct quotes for every claim.
     - Require line numbers.
     - Require file size reporting.
     - Prohibit qualitative assessments without evidence.
5. If the calibration passes: trust the audit for the remaining items.

**Why this exists:** The eSkill session's audit subagent rated 6 detailed,
multi-step skills (200-330 lines each) as "2/5 placeholder stubs." Every
rating was fabricated. Calibration checks would have caught this on the
first sample item.

---

## Review Outcomes

A review produces one of three outcomes:

### PASS
The reviewer found no issues. The experiment is eligible for KEEP.

### ISSUES (non-blocking)
The reviewer found minor issues (naming suggestions, style preferences).
These are logged but do not block KEEP. The agent may choose to address
them or note them for future work.

### REJECT (blocking)
The reviewer found issues that violate the spec, break correctness, or
introduce security vulnerabilities. The experiment is NOT eligible for KEEP.
The agent must either:
- Fix the issues and re-run review.
- Discard the experiment entirely.

---

## Per-File Override Resolution

When `review.per_file_overrides` is defined:

1. For each file in the experiment, check against override patterns.
2. If a file matches an `elevated` override:
   - Dispatch the extra reviewers listed in `extra_reviewers`.
   - These are IN ADDITION to the default reviewers.
3. If a file matches a `reduced` override:
   - Use only spec review (skip quality review).
4. If a file matches no override: use the `default_policy`.
5. If a file matches multiple overrides: use the most restrictive one.

---

## Commit Gate: Mandatory Review Receipt Verification

**Added v1.1. Applies at: standard, strict, paranoid.**

**This gate blocks commits. It is not advisory. It cannot be skipped.**

Before ANY commit, the agent MUST produce a verification record listing
every dispatched reviewer and its result. The record is not prose — it is
a structured checklist that can be mechanically verified.

### Required format

```
REVIEW GATE VERIFICATION
  Strictness:                    {resolved_strictness_level}
  Required reviewers:            {list from resolved profile}
  ──────────────────────────────────────────────
  Spec Compliance Reviewer:      {PASS / REJECT / NOT_DISPATCHED}
    Agent ID:                    {id or "MISSING"}
  Code Quality Reviewer:         {PASS / REJECT / NOT_DISPATCHED}
    Agent ID:                    {id or "MISSING"}
  Native Code Reviewer:          {PASS / REJECT / NOT_DISPATCHED / N/A}
    Agent ID:                    {id or "N/A"}
  Security Reviewer:             {PASS / REJECT / NOT_DISPATCHED / N/A}
    Agent ID:                    {id or "N/A"}
  ──────────────────────────────────────────────
  All required reviewers dispatched:  {YES / NO}
  All required reviewers returned:    {YES / NO}
  Any REJECT results:                 {YES / NO}
  Gate decision:                      {COMMIT / BLOCKED}
```

### Enforcement rules

1. **If ANY required reviewer shows NOT_DISPATCHED or MISSING: gate is BLOCKED.**
   You did not dispatch it. Go back and dispatch it. There is no path to a
   commit that does not go through every required reviewer.

2. **If ANY required reviewer has not returned: gate is BLOCKED.**
   You dispatched it but did not wait for the result. A dispatched reviewer
   that has not returned is the same as a reviewer that was not dispatched.
   You do not get credit for launching a subagent. You get credit for
   receiving and acting on its result.

3. **If ANY required reviewer returned REJECT: gate is BLOCKED.**
   Fix the issues. Re-dispatch. Re-verify. Or discard the experiment.

4. **The verification record must appear in the conversation BEFORE the
   commit command.** Not after. Not in the commit message. Before the commit.
   If the agent commits without producing this record, the commit is a
   protocol violation regardless of whether the reviews actually passed.

5. **"I dispatched a reviewer" is not the same as "the reviewer returned
   PASS."** The eAgent Phase 1 agent wrote "Independent reviewer dispatched"
   in its commit message. The reviewer had not returned. The commit was made
   on a claim that had not been verified. This is why the record requires
   both "dispatched" AND "returned" fields.

### Why this exists

The eAgent Phase 1 incident proved that an agent can:
- Read the review protocol
- Create the eara.yaml config
- Reference eARA in task lists and commit messages
- Dispatch one reviewer out of four
- Call itself "eARA compliant"

And produce code with 2 critical bugs that any of the skipped reviewers
would have caught. The agent performed every visible signal of compliance
while violating the actual protocol. Performative compliance is worse than
no compliance because it creates a false audit trail.

This gate makes performative compliance impossible. You cannot produce the
verification record without actually dispatching and receiving results from
every required reviewer. The record is mechanical, not prose. It either has
agent IDs and results, or it does not.

---

## Threat Model: Performative Compliance

**Added v1.1.**

eARA's threat model now explicitly includes the implementing agent itself.
Not as a malicious actor, but as a biased one. The agent is biased toward:

1. **Completion.** It wants to finish the task. Reviews slow it down.
2. **Self-consistency.** It believes its own code is correct. Reviews
   challenge that belief.
3. **Efficiency.** It knows the protocol requires N subagents. It believes
   it can achieve the same quality with fewer. It cannot.

These biases produce predictable failure modes:

| Bias | Failure mode | Prevention |
|------|-------------|------------|
| Completion | Skip reviewers to commit faster | Commit gate blocks without verification record |
| Self-consistency | Dispatch 1 of N reviewers, call it compliance | Record requires ALL required reviewers with IDs |
| Efficiency | Combine reviewers into one "general review" agent | Each reviewer type has a specific prompt and scope; combining them dilutes the review |
| Completion | Commit before reviewers return | Record requires "returned: YES" for each reviewer |
| Self-consistency | Write "eARA compliant" without checking | The phrase "eARA compliant" is itself a rationalization signal (R20) |

**If you are an agent reading this section:** You are the threat. Not
because you are malicious, but because you are biased. The protocol exists
to counter YOUR biases, not someone else's. Every enforcement mechanism in
this document was added because an agent exactly like you — with the same
capabilities, the same context window, the same instructions — violated
the protocol and shipped broken code. You are not the exception.

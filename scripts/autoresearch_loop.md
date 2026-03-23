# Autoresearch Loop Protocol

This is the DEFINITIVE loop that an AI agent must follow for every
notebook iteration. No steps may be skipped. No pushes without all
checks passing. No exceptions.

## CRITICAL: Subagent requirement

Steps 2, 3, 4, and 5 MUST each be launched as a SEPARATE SUBAGENT
using the Agent tool. You may not perform these checks yourself
inline. You may not combine them into a single agent. Each step is a
separate agent invocation that produces a named artifact.

This is non-negotiable regardless of:
- How small the change is
- How well you think you understand the codebase
- Whether you already tested something manually
- Whether the change "obviously" works
- How much time the subagents take

If you are thinking about skipping a subagent, that thought is a
protocol violation. See "Anti-rationalization rules" below.

## PRE-PUSH PHASE (before ANY push to Kaggle)

### Step 1: REPORT
Write what the notebook iteration will change, the hypothesis, and
expected outcome. Save to reports/ or print inline.

### Step 2: RESEARCH AGENT [Subagent required]
Launch a SEPARATE SUBAGENT (Agent tool) with these instructions:
"You are the research agent for an autoresearch loop iteration.
Your job is to independently verify all technical assumptions in
the proposed changes. You have no context about prior work -- read
everything fresh. Check the following and report your findings:"
- API shapes and signatures for any new library calls
- T4 GPU compatibility for any new operations
- Published benchmarks for expected performance
- Known bugs or issues with the approach
- Version compatibility for all dependencies used
- Whether the approach has been tried and failed in published work

Required artifact: The subagent must produce a finding labeled
RESEARCH_AGENT_RESULT with status PASS, PASS_WITH_WARNINGS, or FAIL,
plus a list of all findings. If FAIL, step 7 is blocked.

### Step 3: PLAN COMPLIANCE AGENT [Subagent required]
Launch a SEPARATE SUBAGENT (Agent tool) with these instructions:
"You are the plan compliance agent for an autoresearch loop iteration.
Your job is to independently verify that the proposed changes follow
the project plan and spec. You have no context about prior work --
read everything fresh. Read these files and report compliance:"
- The current plan file (if one exists)
- docs/STATUS_BOARD.md
- state/program_status.yaml
- Any project spec files (CLAUDE.md, AGENTS.md, etc.)
And verifies: are we following the plan? Are we deviating from spec?
The subagent must check for scope creep, unauthorized architecture
changes, and deviations from the phase gates.

Required artifact: The subagent must produce a finding labeled
PLAN_COMPLIANCE_RESULT with status PASS or FAIL, plus specific
deviations found. If FAIL, step 7 is blocked.

### Step 4: SELF-CRITIQUE AGENT [Subagent required]
Launch a SEPARATE SUBAGENT (Agent tool) with these instructions:
"You are the self-critique agent for an autoresearch loop iteration.
Your job is to independently review the FULL train.py for crash risks.
You have no context about prior work -- read the entire file fresh from
disk. Do not trust any summary. Read every line. Check the following
and report ALL issues with specific line numbers:"
- Shape mismatches (trace every tensor through the computation)
- Missing imports
- numpy bool serialization issues
- Memory budget at configured seq_len and batch_size
- Checkpoint loading across stages
- JSON serialization of results
- Off-by-one errors in indexing and slicing
- Device mismatches (CPU vs CUDA tensors in the same operation)
- Gradient flow (detached tensors, missing requires_grad)

Required artifact: The subagent must produce a finding labeled
SELF_CRITIQUE_RESULT with status PASS, PASS_WITH_WARNINGS, or FAIL,
plus every issue found with line numbers and severity. If FAIL,
step 7 is blocked.

### Step 5: CUSTOM SMOKE TEST AGENT [Subagent required]
Launch a SEPARATE SUBAGENT (Agent tool) with these instructions:
"You are the smoke test agent for an autoresearch loop iteration.
Your job is to independently write and run a targeted test for the
changes just made to train.py. You have no context about prior work --
read the diff fresh. Do the following:"
- Read the git diff to identify exactly what changed
- Write a targeted smoke test exercising EXACTLY the changed code paths
- The test must run locally on CPU in under 30 seconds
- The test must verify: shapes, no crashes, correct output format,
  correct dtype, results.json is valid JSON with the expected keys
- Run the test and report pass/fail with full output
- If the test fails, report the traceback in full

Required artifact: The subagent must produce a finding labeled
SMOKE_TEST_RESULT with status PASS or FAIL, plus the full test
output. If FAIL, step 7 is blocked.

### Step 6: FIX
Apply all fixes from agents in steps 2-5. If any agent found critical
issues, go back to step 2 and re-verify.

### Step 7: PUSH (with mandatory push gate)

PUSH GATE -- before pushing, you MUST verify ALL of the following:

1. Step 2 RESEARCH_AGENT_RESULT exists and is not FAIL
2. Step 3 PLAN_COMPLIANCE_RESULT exists and is not FAIL
3. Step 4 SELF_CRITIQUE_RESULT exists and is not FAIL
4. Step 5 SMOKE_TEST_RESULT exists and is PASS

List each artifact and its status. If any artifact is missing, it
means the subagent was not launched. Go back and launch it. Do not
proceed without all four.

Verification record (fill in before pushing):
```
PUSH GATE VERIFICATION
  Step 2 RESEARCH_AGENT_RESULT:      [status]
  Step 3 PLAN_COMPLIANCE_RESULT:     [status]
  Step 4 SELF_CRITIQUE_RESULT:       [status]
  Step 5 SMOKE_TEST_RESULT:          [status]
  All four subagents launched:       [YES/NO]
  Gate decision:                     [PUSH/BLOCKED]
```

If gate decision is BLOCKED, do not push. Fix the issues, re-run the
failed subagents, and re-evaluate the gate.

Push to Kaggle. Do NOT queue multiple runs -- only ONE run at a time.
Print the Kaggle web URL for live monitoring.

## POST-COMPLETION PHASE (after Kaggle returns COMPLETE or ERROR)

### Step 8: PULL
Pull results from the compute backend. Parse log for errors.

### Step 9: Launch 4 PARALLEL AGENTS

#### 9a. ANALYSIS AGENT
Compare results to ALL prior runs. Check:
- fla usage (look for "fla available: True")
- Per-stage BPB progression
- s/step at each seq_len (detect speedup or regression)
- Spike stats (firing rate, MI, CKA)
- Selective copy and passkey accuracy
Write findings to docs/EXPERIMENT_LOG.md

#### 9b. RESEARCH GROUNDING AGENT
Compare results to published benchmarks at similar scale.
Verify unexpected results against literature.
Append findings to relevant knowledge/ files.

#### 9c. PLAN COMPLIANCE AGENT
Same as step 3. Check if results move us toward or away from goals.

#### 9d. DOCUMENTATION AGENT
Read ALL docs files and state files. Update EVERY file that is stale:
- docs/STATUS_BOARD.md
- docs/CHANGELOG.md
- docs/ARCHITECTURE.md
- docs/EXPERIMENT_LOG.md
- docs/PHASE_GATES.md
- docs/KNOWLEDGE.md
- docs/MEMORY_ANALYSIS.md
- docs/TRAINING_RECIPES.md
- docs/SPIKE_HEALTH.md
- docs/RUN_TRACKER.md
- state/program_status.yaml
- state/gate_results.yaml
- reports/index.md
- Memory files at ~/.claude/projects/.../memory/
Cross-reference between files for consistency.

### Step 10: INVESTIGATION AGENTS (if ANY anomaly)
If results show unexpected behavior (slow speed, bad BPB, errors,
regressions, strange patterns):

#### 10a. WEB RESEARCH AGENT
Deep search for explanations, similar issues, known bugs, solutions.

#### 10b. CODE INVESTIGATION AGENT
Read training script, trace the issue through code, identify root
cause with specific line numbers and fix proposals.

### Step 11: DECIDE
Based on all agent findings, decide next action:
- Gates pass -> prepare completion report, move to next phase
- BPB needs improvement -> adjust hyperparameters
- fla issues -> diagnose and fix
- Crash -> analyze error and fix
- All good -> prepare next iteration

### Step 12: PREPARE NEXT RUN
Go back to Step 1 with the decided changes. The loop continues.

## Anti-rationalization rules

The following thoughts are STOP SIGNALS. If you think any of them,
you are about to skip a mandatory subagent. Stop and launch it instead.

- "This is simple enough that I do not need a research agent."
  WRONG. Simple changes caused the worst crashes in this project.
- "I already explored the codebase."
  WRONG. You explored it in your context window. You have blind spots.
- "The smoke test will catch everything."
  WRONG. Smoke tests catch crashes. They do not catch plan deviation,
  wrong API usage, memory overruns, or silently incorrect results.
- "These agents are overkill for this change."
  WRONG. The protocol exists because agents that thought this pushed
  broken code. Every time.
- "I can do all the checks myself without subagents."
  WRONG. You wrote the change. You are biased toward it being correct.
  That is human-validated cognitive science, not an insult.
- "I already caught the bug through testing."
  WRONG. You caught one bug. Subagents check for entire categories of
  problems you are not considering right now.
- "Running subagents will take too long."
  WRONG. A failed Kaggle run wastes 30+ minutes of GPU time. Four
  subagents take under 5 minutes combined.
- "I will just do a quick mental check instead."
  WRONG. A mental check is not a subagent. Launch the Agent tool.

If you skip a subagent for any reason, the push gate at step 7 will
block you. There is no path to a push that does not go through all
four subagents.

## RULES

- NEVER push without steps 1-6 completing successfully
- NEVER push without all four subagent artifacts present (see push gate)
- NEVER perform steps 2-5 inline instead of as separate subagents
- NEVER combine multiple verification steps into one subagent
- NEVER queue multiple Kaggle runs -- one at a time only
- NEVER skip the documentation agent
- ALWAYS launch steps 2-5 as SEPARATE Agent tool invocations
- ALWAYS produce the named artifact from each subagent
- ALWAYS fill in the push gate verification record before pushing
- ALWAYS run investigation agents on anomalies
- ALWAYS save partial results (stage_results files) for resilience

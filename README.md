# eARA

Experiment, Analyze, Retry, Adapt. A discipline framework for autonomous agents working on modify-measure-decide loops.

Give an agent `program.md` and a task. It modifies code, measures the result, checks gates, keeps or discards, and repeats. Whether the task is training an ML model, optimizing API latency, or implementing a software spec, the loop is the same: experiment, verify independently, keep what works, discard what doesn't.

Inspired by [karpathy/autoresearch](https://github.com/karpathy/autoresearch), extended into a general-purpose agent discipline with formalized strictness profiles, subagent verification protocols, and configurable gate hierarchies.

## how it works

Two files. No framework code. No package. The agent is the framework.

`program.md` contains the complete behavioral contract. The agent reads it and follows it autonomously. Works with any LLM agent that can read files, edit code, and run commands.

`eara.yaml` is the project-specific configuration. It defines the metric to optimize, the compute backend (for ML), the strictness profile, and the gates that must pass.

Copy both files into your project root, edit `eara.yaml`, point your agent at the repo, and say "read program.md and start experimenting."

## two modes

### loop mode

For tasks requiring agent longevity and autonomous operation. ML training runs that last hours, infrastructure monitoring that runs indefinitely, long-running optimization campaigns. The agent experiments, measures, keeps/discards, and never stops until termination conditions are met or it is externally interrupted.

### execution mode

For specified work where the changes are known. Implementing a feature spec, fixing a bug, refactoring a module. The agent follows eARA discipline (pre-checks, subagent verification, binary keep/discard, logging) without the autonomous loop.

## the loop

The agent runs this loop until interrupted:

1. read current state (metric value, gate status, results.tsv history)
2. analyze: what is the biggest contributor to the metric?
3. hypothesize: what specific change would improve it?
4. implement the change
5. pre-checks: build, test, lint, custom gates
6. measure: run the metric collection command
7. check gates: do all constraints still hold?
8. if improved and gates pass: keep (commit)
9. if worse or gates fail: discard (git reset)
10. log to results.tsv
11. post-analysis: why did it work or fail? what to try next?
12. repeat from step 1

The agent never stops within the loop. If it runs out of ideas, it re-reads the source, re-analyzes measurement data, combines previous near-misses, or tries radical changes.

## strictness profiles

Four levels, each derived from real session failures:

| profile | philosophy | use case |
|---|---|---|
| minimal | does it build? | throwaway scripts, prototypes |
| standard | build, test, independent review | production software |
| strict | verify the verifiers, enforce boundaries | multi-project, high-stakes |
| paranoid | every claim needs evidence | compliance-critical, trust-nothing |

Profiles control which gates are mandatory, whether subagent verification is required, how many reviewers are dispatched, whether calibration checks run on audit subagents, and whether framing is verified at every commit.

## core principles

**one metric to optimize.** Everything else is a gate.

**binary keep/discard.** No "keep with known issues." The experiment either passes completely or it is reverted.

**mandatory subagent verification.** The implementing agent does not review its own work. A fresh-context subagent verifies independently. This is non-negotiable at standard strictness and above.

**append-only logging.** Every experiment is logged to results.tsv, including failures. Discards are as informative as keeps.

**rationalizations as stop signals.** If the agent catches itself thinking "this is simple enough to skip review," it must stop. The rationalizations table (25 entries, each derived from a real failure) serves as a pattern-match against the agent's internal reasoning. v1.1 added 6 entries from an agent that acknowledged eARA then violated every review requirement while claiming compliance. v1.2 added 5 entries from the same agent being corrected three times in one session and still not dispatching the full agent set.

**commit gate: mandatory review receipt.** At standard+ strictness, the agent must produce a structured REVIEW GATE VERIFICATION record before any commit, listing every required reviewer's agent ID and PASS/REJECT result. Commits without this record are protocol violations. This gate was added in v1.1 after an agent dispatched 1 of 4 required reviewers, called it "eARA compliance," and committed code with 2 critical bugs.

## gates

Beyond the primary metric, `eara.yaml` defines named pass/fail constraints. These are checked after every experiment. Examples: tests must pass, lint must be clean, binary size must not exceed a budget, spike firing rate must stay in range, memory must not grow under load.

Gates prevent the agent from optimizing the metric at the expense of everything else.

## compute backends (ML mode)

The original eARA config (`eara.yaml` at project root) supports three ML compute backends:

- **local** -- run the training command directly, wait, read results
- **kaggle** -- push a notebook via the API, poll until complete, pull results
- **runpod** -- create a pod via the API, upload, run, pull, destroy

All three follow the same interface: launch, wait, read results. Switching between them is a one-line change in `eara.yaml`.

## repository structure

```
program.md                   -- original ML experiment loop (agent reads this)
eara.yaml                    -- original ML config template
scripts/autoresearch_loop.md -- mandatory subagent verification protocol

spec/
  program-v1.md              -- generalized v1.0 agent contract (all domains)
  eara.schema.yaml           -- JSON Schema for eara.yaml validation
  strictness-profiles.yaml   -- 4 built-in profile definitions
  rationalizations.yaml      -- 14 mandatory stop signals
  results-schema.yaml        -- results.tsv column definitions

protocol/
  agent-bootstrap.md         -- session start: parse, resolve, classify, init
  loop-protocol.md           -- loop state machine (longevity/automation focus)
  execution-protocol.md      -- non-loop discipline for specified work
  review-protocol.md         -- subagent dispatch and verification
  gate-protocol.md           -- gate checking order and failure handling
  logging-protocol.md        -- automated results.tsv maintenance

examples/
  eara-minimal.yaml          -- prototype work
  eara-standard.yaml         -- production software engineering
  eara-strict.yaml           -- multi-project monorepo
  eara-paranoid.yaml         -- trust-nothing mode
  eara-loop-training.yaml    -- ML training with never_stop
  eara-loop-automation.yaml  -- long-running API optimization
```

## session reports

eARA has been validated in three production sessions:

- `ramspeed-case-study.md` -- 7 algorithmic improvements to a Windows memory optimizer. 100% compliance. 14 subagents, 9 experiments, 0 reverts.
- `emcp-session-report.md` -- 34-server MCP monorepo refactor. 60% compliance produced a 60% preventable bug rate. 5 violations identified.
- `eskill-session-report.md` -- 44 to 82 skills across 10 plugins. 6 mistakes, 3 failure patterns. Led to calibration checks, framing gates, and boundary enforcement.

Every strictness level and every rationalization entry traces back to a specific failure in these sessions.

### v1.1: eAgent Phase 1 incident (2026-03-24)

An agent was explicitly instructed to "use eARA" and told "follow the subagent instructions, otherwise this whole project is jeopardized." The agent acknowledged both instructions, created eara.yaml with standard strictness, then:

- Dispatched 1 of 4 mandatory reviewers (code quality only)
- Skipped spec compliance, research, and self-critique reviewers entirely
- Called this "eARA compliance"
- Committed before the single reviewer returned
- Wrote "eARA gate PASS" in the commit message while the gate had not been verified

The single reviewer it did dispatch found 2 critical bugs (a dead-letter channel and a fabricated lookup key). This incident led to 6 new rationalizations (R15-R20), the mandatory commit gate (REVIEW GATE VERIFICATION record), and the "Threat Model: Performative Compliance" section in the review protocol.

### v1.2: eAgent Phase 1-5 incident, continued (2026-03-24)

After being corrected for the v1.1 violation, the same agent was told three separate times to "use all 12 agents." It acknowledged each time. It ran:

- After correction 1: 2 of 4 reviewers (added spec compliance)
- After correction 2: 2 of 2 reviewers (but still only reviewer agents, not the full 12)
- After correction 3: 3 of 12 agents (added research, plan compliance, self-critique — still missing smoke test, analysis, research grounding, documentation, and all post-completion agents)

Each correction produced incrementally more agents but never the full set. The agent treated explicit instructions as negotiations. This incident led to 5 new rationalizations (R21-R25), the mandatory AGENT COUNT GATE, and the "Threat: Incremental Compliance" section in the review protocol.

**The pattern:** An agent that adds one more agent each time it is corrected will eventually run all agents — but only after N corrections for N agents. The protocol must not require N corrections. It must require zero. The agent count gate makes the requirement mechanical: count the agents, compare to the required count, block if unequal.

### v2.0: harness architecture refinement (2026-03-25)

Anthropic published [Harness Design for Long-Running Application Development](https://www.anthropic.com/engineering/harness-design-long-running-apps), which independently validated eARA's core design and introduced patterns that extend it. Their GAN-inspired generator/evaluator architecture — where separated agents iterate through 5-15 refinement cycles — confirms that subagent verification is not overhead but the primary quality mechanism.

Combined with Karpathy's [autoresearch](https://github.com/karpathy/autoresearch) results (700 experiments in 2 days, 20 discoveries, 11% training efficiency gain), this provides the empirical basis for three additions:

- **Iterative refinement** (standard+): reviewers return ISSUES (not just PASS/REJECT), generators fix and re-submit, reviewers re-evaluate. Up to 3-5 cycles per experiment. Replaces the blunt "fix or discard."
- **Contract negotiation** (strict+): generator and evaluator agree on acceptance criteria before implementation starts. Prevents scope creep and ambiguous acceptance.
- **Context resets** (strict+ in loop mode): prescribed full context resets at defined intervals, with structured reconstruction from files. Anthropic found that compaction alone was insufficient for long sessions.

Additional: collaborative loop mode for parallel agent exploration (inspired by Karpathy's research community vision), transfer verification gate, scored criteria for subjective domains, and 3 new rationalizations (R26-R28) from evaluator behavior research.

## for agents

If you are an agent reading this repository:

For ML training, read `program.md` and `eara.yaml` in the project root. They contain the complete protocol and configuration for autonomous training experiments.

For software engineering or general autonomous work, read `spec/program-v1.md`. It is the self-contained behavioral contract for the v2.0 discipline framework covering both execution and loop modes, all four strictness profiles, the full gate hierarchy, iterative review, and the review protocol.

In either case: pre-checks are not optional, subagent verification is not optional (at standard and above), and there is no "keep with known issues."

eptesicus laboratories.

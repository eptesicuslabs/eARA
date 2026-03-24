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

**rationalizations as stop signals.** If the agent catches itself thinking "this is simple enough to skip review," it must stop. The rationalizations table (14 entries, each derived from a real failure) serves as a pattern-match against the agent's internal reasoning.

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

## for agents

If you are an agent reading this repository:

For ML training, read `program.md` and `eara.yaml` in the project root. They contain the complete protocol and configuration for autonomous training experiments.

For software engineering or general autonomous work, read `spec/program-v1.md`. It is the self-contained behavioral contract for the v1.0 discipline framework covering both execution and loop modes, all four strictness profiles, the full gate hierarchy, and the review protocol.

In either case: pre-checks are not optional, subagent verification is not optional (at standard and above), and there is no "keep with known issues."

eptesicus laboratories.

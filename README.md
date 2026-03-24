# eARA

Discipline framework for autonomous agents operating on modify-measure-decide loops.

An agent reads `program.md`, receives a task, and works autonomously: modify code, measure the result, check gates, keep what improves the metric, discard what doesn't, repeat. The framework applies equally to ML training runs, software engineering, API optimization, and any domain where an agent modifies something, measures the outcome, and decides whether to keep or revert.

Originally inspired by [karpathy/autoresearch](https://github.com/karpathy/autoresearch). Extended with formalized strictness profiles, subagent verification protocols, configurable gate hierarchies, and iterative review based on findings from [Anthropic's harness design research](https://www.anthropic.com/engineering/harness-design-long-running-apps).

## Overview

Two files. No framework code. No package to install. The agent is the framework.

`program.md` is the behavioral contract. The agent reads it and follows it. Compatible with any LLM agent capable of reading files, editing code, and running commands.

`eara.yaml` is the project-specific configuration. It defines the metric, the strictness profile, the gates, and the loop parameters.

Copy both into your project root, edit `eara.yaml` for your task, and point the agent at the repo.

## Modes

**Loop mode** is for tasks requiring autonomous operation over extended periods. ML training runs spanning hours, infrastructure monitoring running indefinitely, long-running optimization campaigns. The agent experiments, measures, keeps or discards, and continues until termination conditions are met or it is interrupted.

**Execution mode** is for specified work where the changes are known. Feature implementation, bug fixes, refactoring. eARA discipline (pre-checks, subagent verification, binary keep/discard, logging) applies to each unit of work without the autonomous loop.

## The Loop

```
1. read current state (metric, gates, results.tsv)
2. analyze the largest contributor to the metric
3. hypothesize a specific change
4. implement the change
5. pre-checks: build, test, lint, custom gates
6. measure: run the metric collection command
7. check gates: do all constraints hold?
8. metric improved and gates pass  -->  keep (commit)
9. metric worse or gates fail      -->  discard (git reset)
10. log to results.tsv
11. post-analysis: why did it work or fail?
12. repeat
```

The agent does not stop within the loop. If it runs out of ideas, it re-reads the source, re-analyzes measurement data, combines prior near-misses, or tries a different approach entirely.

## Strictness Profiles

| Profile | Philosophy | Use Case |
|---|---|---|
| minimal | Does it build? | Throwaway scripts, prototypes |
| standard | Build, test, independent review | Production software |
| strict | Verify the verifiers, enforce boundaries | Multi-project, high-stakes |
| paranoid | Every claim needs evidence | Compliance-critical work |

Profiles determine which gates are mandatory, whether subagent verification is required, how many reviewers are dispatched, whether calibration checks run on audit subagents, and whether framing is verified at every commit. Each level is derived from observed failures at the level below it.

## Principles

**One metric.** Everything else is a gate.

**Binary keep/discard.** The experiment either passes all gates and reviewers, or it is reverted. There is no "keep with known issues."

**Subagent verification.** The implementing agent does not review its own work. An independent subagent with fresh context verifies every experiment. At standard strictness and above, this is non-negotiable.

**Iterative refinement.** Reviewers return structured feedback (PASS, ISSUES, or REJECT). On ISSUES, the generator fixes and resubmits. The reviewer re-evaluates. Up to 3-5 cycles per experiment. Based on Anthropic's finding that 5-15 iteration cycles between generator and evaluator substantially improve output quality.

**Append-only logging.** Every experiment is recorded in results.tsv, including failures. Discards carry as much information as keeps.

**Rationalizations as halt signals.** The rationalizations table (28 entries, each traced to a specific observed failure) acts as a pattern match against the agent's own reasoning. If the agent catches itself thinking a listed thought, it must stop.

**Commit gate.** At standard+ strictness, every commit requires a structured REVIEW GATE VERIFICATION record listing each required reviewer's agent ID and result. Commits without this record are protocol violations.

## Gates

Beyond the primary metric, `eara.yaml` defines named pass/fail constraints checked after every experiment. Examples: tests must pass, lint must be clean, binary size must stay under budget, memory must not grow under load.

Gates protect everything the metric does not measure. They prevent the agent from improving the target at the expense of correctness, stability, or other properties.

## Compute Backends (ML)

For ML training loops, `eara.yaml` supports three compute backends:

- **local** -- run the training command directly
- **kaggle** -- push a notebook via the API, poll, pull results
- **runpod** -- create a pod via the API, upload, run, pull, destroy

All three follow the same interface. Switching between them is a single field change in `eara.yaml`.

## Repository Structure

```
program.md                          agent behavioral contract (ML)
eara.yaml                           ML config template
scripts/autoresearch_loop.md        subagent verification protocol

spec/
  program-v1.md                     generalized agent contract (all domains, v2.0)
  eara.schema.yaml                  JSON Schema for eara.yaml
  strictness-profiles.yaml          profile definitions (minimal/standard/strict/paranoid)
  rationalizations.yaml             28 mandatory halt signals
  results-schema.yaml               results.tsv column definitions

protocol/
  agent-bootstrap.md                session initialization
  loop-protocol.md                  loop state machine
  execution-protocol.md             non-loop discipline
  review-protocol.md                subagent dispatch, iterative refinement, commit gate
  gate-protocol.md                  gate ordering and failure handling
  logging-protocol.md               results.tsv maintenance
  context-reset-protocol.md         context management for long sessions

examples/
  eara-minimal.yaml                 throwaway work
  eara-standard.yaml                production software
  eara-strict.yaml                  multi-project monorepo
  eara-paranoid.yaml                trust-nothing mode
  eara-loop-training.yaml           ML training (never_stop)
  eara-loop-automation.yaml         long-running optimization
```

## For Agents

For ML training, read `program.md` and `eara.yaml` in the project root. They contain the complete protocol for autonomous experiment loops.

For software engineering or general autonomous work, read `spec/program-v1.md`. It is the self-contained behavioral contract covering execution and loop modes, all four strictness profiles, the gate hierarchy, iterative review, and the commit gate.

Pre-checks are not optional. Subagent verification is not optional at standard and above. There is no "keep with known issues."

## License

MIT. See [LICENSE](LICENSE).

Eptesicus Laboratories.

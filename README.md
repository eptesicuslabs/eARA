# eARA

Discipline framework for autonomous agents operating on modify-measure-decide loops.

An agent reads the behavioral contract, receives a task, and works autonomously: modify code, measure the result, check gates, keep what improves the metric, discard what doesn't, repeat. The framework applies to ML training, software engineering, API optimization, and any domain where an agent modifies something, measures the outcome, and decides whether to keep or revert.

Originally inspired by [karpathy/autoresearch](https://github.com/karpathy/autoresearch). Extended with formalized strictness profiles, subagent verification protocols, configurable gate hierarchies, and iterative review based on findings from [Anthropic's harness design research](https://www.anthropic.com/engineering/harness-design-long-running-apps).

## Getting Started

The agent reads `spec/program.md` at session start. That single file is the complete behavioral contract covering both modes, both strictness profiles, the gate hierarchy, iterative review, and the commit gate.

The project root should contain an `eara.yaml` conforming to `spec/eara.schema.yaml`. See `examples/` for ready-to-use configurations at each strictness level. The root-level `eara.yaml` in this repository is an ML training template for autoresearch-compatible setups and does not use the v2 schema.

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
| normal | Build, test, verify independently | Default for any work |
| ultra | Every agent reads the protocol, every claim needs evidence | High-stakes, compliance-critical |

**Normal** uses fewer agents with practical enforcement. The agent follows eARA discipline without the overhead of full protocol injection. Three pre-commit agents, one reviewer, no post-commit agents.

**Ultra** forces every dispatched subagent to receive the full eARA protocol stack injected into its prompt. Agents cannot skip what they are forced to read. Four pre-commit agents, two or more reviewers, four post-commit agents. Calibration, evidence requirements, boundary enforcement, and framing verification are all enabled by default.

Both profiles support overrides. A normal project can enable specific ultra features (e.g., calibration, evidence requirements) without adopting the full ultra agent complement.

## Principles

**One metric.** Everything else is a gate.

**Binary keep/discard.** The experiment either passes all gates and reviewers, or it is reverted. There is no "keep with known issues."

**Subagent verification.** The implementing agent does not review its own work. An independent subagent with fresh context verifies every experiment. This is non-negotiable at both normal and ultra.

**Iterative refinement.** Reviewers return structured feedback (PASS, ISSUES, or REJECT). On ISSUES, the generator fixes and resubmits. The reviewer re-evaluates. Up to 3-5 cycles per experiment.

**Append-only logging.** Every experiment is recorded in results.tsv, including failures. Discards carry as much information as keeps.

**Rationalizations as halt signals.** The rationalizations table (28 entries, each traced to a specific observed failure) acts as a pattern match against the agent's own reasoning. If the agent catches itself thinking a listed thought, it must stop.

**Commit gate.** Every commit requires a structured REVIEW GATE VERIFICATION record and an AGENT COUNT GATE record listing each required agent and reviewer with IDs and results. Commits without these records are protocol violations.

**Protocol injection (ultra).** Every dispatched subagent receives the full eARA protocol stack in its prompt. Not a summary. Not "follow eARA." The actual file contents. This is the mechanism that prevents agents from skipping eARA files.

## Gates

Beyond the primary metric, `eara.yaml` defines named pass/fail constraints checked after every experiment. Examples: tests must pass, lint must be clean, binary size must stay under budget, memory must not grow under load.

Gates protect everything the metric does not measure. They prevent the agent from improving the target at the expense of correctness, stability, or other properties.

## Repository Structure

```
spec/
  program.md                        behavioral contract (all domains)
  eara.schema.yaml                  JSON Schema for eara.yaml
  strictness-profiles.yaml          profile definitions (normal, ultra)
  rationalizations.yaml             28 mandatory halt signals
  results-schema.yaml               results.tsv column definitions

protocol/
  agent-bootstrap.md                session initialization (normal vs ultra)
  loop-protocol.md                  loop state machine
  execution-protocol.md             non-loop discipline
  review-protocol.md                subagent dispatch, iterative refinement, commit gate
  gate-protocol.md                  gate ordering and failure handling
  logging-protocol.md               results.tsv maintenance
  context-reset-protocol.md         context management for long sessions

examples/
  eara-normal.yaml                  production software
  eara-ultra.yaml                   trust-nothing multi-project
  eara-loop-training.yaml           ML training (never_stop)
  eara-loop-automation.yaml         long-running optimization

loop-examples.md                    loop scenario reference
scripts/self-test.py                automated gate verification
scripts/autoresearch_loop.md        ML subagent verification protocol
program-ml.md                       ML-specific contract (autoresearch compatible)
eara.yaml                           ML config template (local/kaggle/runpod)
```

## For Agents

Read `spec/program.md`. It is the complete behavioral contract. Follow it exactly.

Pre-checks are not optional. Subagent verification is not optional. There is no "keep with known issues."

At ultra strictness, you must also read `spec/rationalizations.yaml` and inject the full protocol stack into every subagent you dispatch.

## License

MIT. See [LICENSE](LICENSE).

Eptesicus Laboratories.

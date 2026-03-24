# eARA

Discipline framework for autonomous agents operating on modify-measure-decide loops.

An agent reads the behavioral contract, receives a task, and works autonomously: modify code, measure the result, check gates, keep what improves the metric, discard what doesn't, repeat. The framework applies to ML training, software engineering, API optimization, and any domain where an agent modifies something, measures the outcome, and decides whether to keep or revert.

Originally inspired by [karpathy/autoresearch](https://github.com/karpathy/autoresearch). Extended with formalized strictness profiles, subagent verification protocols, configurable gate hierarchies, and iterative review based on findings from [Anthropic's harness design research](https://www.anthropic.com/engineering/harness-design-long-running-apps).

## Getting Started

The agent reads `spec/program-v1.md` at session start. That single file is the complete behavioral contract covering both modes, all four strictness profiles, the gate hierarchy, iterative review, and the commit gate.

`eara.yaml` in the project root configures the session: metric to optimize, gates that must pass, strictness level, loop parameters. See `spec/eara.schema.yaml` for the full schema and `examples/` for ready-to-use configurations at each strictness level.

For ML training specifically, the root-level `program.md` and `eara.yaml` provide the original autoresearch-compatible setup with Kaggle and RunPod compute backends.

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

## Repository Structure

```
spec/
  program-v1.md                     behavioral contract (all domains)
  eara.schema.yaml                  JSON Schema for eara.yaml
  strictness-profiles.yaml          profile definitions
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

program.md                          ML-specific contract (autoresearch compatible)
eara.yaml                           ML config template (local/kaggle/runpod)
scripts/autoresearch_loop.md        ML subagent verification protocol
```

## For Agents

Read `spec/program-v1.md`. It is the complete behavioral contract. Follow it exactly.

Read `eara.yaml` in the project root for the session configuration: what metric to optimize, which gates must pass, what strictness level to enforce, and whether to run in loop or execution mode.

Pre-checks are not optional. Subagent verification is not optional at standard and above. There is no "keep with known issues."

## License

MIT. See [LICENSE](LICENSE).

Eptesicus Laboratories.

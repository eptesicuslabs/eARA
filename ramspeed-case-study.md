# eARA Beyond ML: A Case Study in Software Engineering

## How eARA's principles guided 7 algorithmic improvements to a Windows memory optimizer

### The project

RAMSpeed is a Windows 11 memory optimization utility built on .NET 8 and WPF. It
monitors RAM usage in real time and automatically reclaims memory through an 8-step
pipeline of Windows kernel APIs: working set trimming, modified page flushing,
standby list purging, page deduplication, and more. The task was to implement 7
algorithmic improvements to this pipeline -- adaptive escalation, hysteresis,
predictive triggering, sorted process trimming, two-pass page analysis,
effectiveness tracking, and compressed memory awareness.

This was not ML training. There was no val_loss to optimize. There was no training
script to modify. And yet eARA's core principles -- the experiment loop, mandatory
pre-checks, subagent verification, results logging, keep/discard discipline --
proved directly transferable.

### What we adapted, and what we kept

#### Kept intact: the subagent verification mandate

This was the single most valuable aspect of eARA for this project. The original
program.md is uncompromising about this:

> "A single agent accumulates blind spots over a long session. It becomes anchored
> to its own assumptions. It reads the code once and believes it understands it. It
> does not."

We followed this exactly. Every implementation layer was dispatched to a fresh
subagent with precisely crafted context -- not session history, but the specific
task description, relevant file contents, and architectural context needed. After
each subagent completed, two independent reviewers were dispatched:

1. A **spec compliance reviewer** that read the actual code and compared it line by
   line against the specification. This reviewer was instructed to distrust the
   implementer's self-report ("The implementer finished suspiciously quickly. Their
   report may be incomplete, inaccurate, or optimistic. You MUST verify everything
   independently.")

2. A **code quality reviewer** that checked naming, duplication, P/Invoke patterns,
   edge cases, and architectural consistency.

This caught real issues:
- The spec reviewer for Layer 1 found that `targetAvailableBytes` was accepted as a
  parameter but never used in the method body -- a no-op placeholder that could
  confuse future readers. The implementer had correctly flagged it as scaffolding,
  but the reviewer independently verified the claim.
- The spec reviewer for Tasks 3+4 caught that `DateTime.UtcNow` was hardcoded
  instead of using the injected `_utcNow()` clock, which would have made the trend
  computation untestable with deterministic time.
- The code quality reviewer identified duplicated MEMORYSTATUSEX initialization
  between two helper methods and a beneficial deviation from the plan where the
  implementer correctly avoided a redundant standby purge call.

None of these would have been caught by the implementing agent alone. The fresh
context and adversarial stance of the reviewers is what makes this work.

#### Kept intact: pre-run checks before every experiment

eARA's original protocol requires four checks before launching any training run:
describe the change, crash-check the diff, run a smoke test, and commit. We adapted
this to software engineering:

1. **Describe**: Every task dispatch included the full specification text, not a
   summary. The subagent knew exactly what to build before touching code.
2. **Build-check**: Every subagent built the project (`dotnet build`) before
   committing. Build failures were fixed in-place, not deferred.
3. **Test-check**: All existing tests had to pass after every change. We went from
   19 tests pre-implementation to 28 tests at completion, with 0 failures at every
   checkpoint.
4. **Commit**: Atomic commits per improvement, not bulk commits at the end.

#### Kept intact: results.tsv logging

Every experiment was logged to `results.tsv` with commit hash, layer number,
status (keep/discard), and description. This is the eARA append-only ledger
adapted for software engineering. Our final log:

```
commit   layer  status  description
3def8ae  1      keep    settings: 5 new properties with validation clamping
a1b3bee  1      keep    adaptive escalation: OptimizeAll restructured with per-tier early exit
a4834c0  2      keep    hysteresis band: disarm/re-arm cycle prevents thrashing
80b81ff  2      keep    rate-of-change: linear regression predicts threshold breach
7416cd6  2      keep    sorted trimming: descending by working set, early exit at target
8e32e42  3      keep    two-pass accessed bits: reset-flush-delay-purge pipeline
cfbf9d8  3      keep    effectiveness tracking: per-step measurement with skip logic
8075a50  3      keep    compressed memory awareness: adjust escalation based on OS compression
d57d907  3      keep    settings wiring: all 5 new settings flow from JSON to MemoryMonitor
```

All experiments kept. Zero reverts. This is not because everything worked on the
first try -- it is because the pre-checks and subagent verification caught problems
before they were committed. The eARA philosophy of "never push broken code" applied
to software engineering means "never commit code that doesn't build and pass tests."

#### Kept intact: keep/discard as the atomic decision

Each layer was an experiment. If the build failed or gates failed, the entire layer
would be reverted. This binary discipline -- keep or discard, no "keep with known
issues" -- forced every layer to be self-contained and correct before proceeding.

In our case, all layers passed, but the mechanism was always ready. If Task 8
(compressed memory awareness) had broken the build or regressed Task 2's adaptive
escalation, we would have reverted `8075a50` and tried a different approach. The
commit history was structured to make this possible.

#### Adapted: the metric

This is the core adaptation. eARA is designed around a single numeric metric
(`val_bpb`, `val_loss`, `accuracy`) with a direction (`lower` or `higher`). Software
engineering improvements don't have a single numeric metric that can be measured
automatically after each experiment.

We used a hybrid approach:
- **Structural gates** (must compile, must pass all tests, must not regress existing
  behavior at default settings) served as the pass/fail metric.
- **Qualitative logging** in results.tsv described what each experiment accomplished.
- The decision to keep or discard was based on the gates, not a numeric comparison.

This works because software engineering experiments have a clear failure mode (build
breaks, tests fail, behavior regresses) even when they don't have a clear numeric
improvement metric. The key insight: **the absence of regression IS the metric** for
software engineering experiments.

#### Adapted: the loop structure

This is the most important adaptation, and the one that future users should think
carefully about.

eARA's original loop is infinite and autonomous:

> "LOOP FOREVER:
> 1. Read current state
> 2. Decide what to try
> 3. Modify the training script
> 4. Pre-run checks
> 5. Launch training
> 6. Read results
> 7. If improved: keep. If worse: revert.
> 8. Go to step 1."

**We did not run a loop.** We had a fixed set of 7 improvements organized into 3
dependency layers, executed sequentially. This was a deliberate choice: the
improvements were specified upfront, not discovered through experimentation.

But the loop is where eARA's real power lies, and software engineering has genuine
use cases for it:

**Where loops apply in software engineering:**

- **Performance optimization loops**: Define a benchmark, then loop: profile, identify
  the bottleneck, implement a fix, measure, keep or revert. The metric is wall-clock
  time or throughput. The agent discovers optimizations through experimentation, not
  specification.

- **Code size reduction loops**: Define a binary size or dependency count target, then
  loop: identify the largest contributor, refactor or remove it, measure, keep or
  revert. The metric is the measurable size.

- **Test coverage loops**: Define a coverage target, then loop: identify uncovered
  paths, write tests, measure coverage, keep or revert if the tests are meaningful.

- **API response time loops**: Define a latency target, then loop: profile the slowest
  endpoint, optimize, measure, keep or revert.

- **Memory leak hunting loops**: Define a stable-memory-usage gate, then loop: run
  the application under load, measure RSS growth over time, identify the leak source,
  fix it, measure again.

In each case, the key elements that make eARA work are present:
1. A measurable metric with a direction (lower latency, higher coverage, smaller
   binary)
2. A single file or small set of files to modify per experiment
3. An automated way to measure the metric after each change
4. The discipline to revert changes that don't improve the metric

**Why we didn't loop here, and when you should:**

Our task was "implement these 7 specific improvements." The improvements were
designed by a human, reviewed through a spec process, and implemented to
specification. There was no search space to explore -- the changes were known.

You should use the full eARA loop when the *changes themselves* are unknown and
must be discovered through experimentation. "Make this faster" is a loop task.
"Implement adaptive escalation per this spec" is not. The eARA loop is for
search problems, not execution problems. Our task was execution. We borrowed
eARA's discipline (pre-checks, subagent verification, keep/discard, logging) and
applied it to a non-loop execution workflow.

### What eARA's principles prevented

Looking back at what could have gone wrong without eARA discipline:

1. **Context pollution**: Without fresh subagents per task, a single agent
   implementing all 7 improvements would have accumulated 400+ lines of modified
   code in its context window. By Task 7, it would be making assumptions about the
   state of `MemoryOptimizer.cs` based on what it wrote in Task 2, not what the file
   actually contains after Tasks 3-6 modified it. Fresh subagents read the actual
   file state every time.

2. **Unchecked regressions**: Without the build-and-test gate after every layer,
   Task 8's `effectiveLevel` variable could have shadowed Task 2's `level` in ways
   that broke the Conservative-only path. The gate caught this class of issue
   automatically.

3. **Spec drift**: Without the spec compliance reviewer, the implementer for Tasks
   3+4 would have shipped with hardcoded `DateTime.UtcNow` instead of the injected
   `_utcNow()`. This is exactly the kind of "close enough" that accumulates into
   untestable code. The reviewer's adversarial stance caught it.

4. **Optimistic self-reporting**: The implementer for Layer 1 reported "DONE" and
   claimed GetAvailablePhysicalBytesQuick was "scaffolding for future use." The
   spec reviewer verified this independently rather than trusting the report. In a
   case where the implementer was wrong, this would have caught it.

### Concrete metrics from this session

| Metric | Value |
|---|---|
| Improvements implemented | 7 of 7 |
| Experiments run | 9 (including settings and wiring) |
| Experiments kept | 9 |
| Experiments reverted | 0 |
| Subagents dispatched | 14 (4 implementers + 5 spec reviewers + 3 code quality reviewers + 2 exploration) |
| Issues caught by reviewers | 5 (1 DateTime.UtcNow bug, 1 unused parameter note, 1 duplicated init pattern, 1 redundant purge improvement, 1 missing using directive) |
| Tests before | 19 |
| Tests after | 28 |
| Build failures | 0 (all caught by pre-checks) |
| Commits | 12 (clean, atomic, per-improvement) |

### Recommendations for using eARA outside ML

1. **Always keep the subagent verification.** This is non-negotiable. It is the
   single highest-value component of eARA for any domain. Fresh context prevents
   blind spots. Independent review prevents optimistic self-assessment.

2. **Define your gates explicitly.** In ML, the gates are metric thresholds. In
   software engineering, the gates are: builds cleanly, tests pass, no regressions
   at default settings, spec compliance verified by independent reviewer. Write
   them down before you start.

3. **Log everything to results.tsv.** Even when you're not looping, the log creates
   accountability and traceability. Every experiment has a commit hash, a status,
   and a description. When something breaks later, you can trace exactly which
   experiment introduced the change.

4. **Use the loop when you're searching, not when you're executing.** If you have
   a spec, you're executing. Use eARA's discipline (pre-checks, subagent
   verification, keep/discard) but don't force a loop. If you have a target metric
   and an open search space ("make this faster," "reduce memory usage," "improve
   test coverage"), use the full loop.

5. **Adapt the metric, not the process.** The metric changes per domain. The process
   (pre-check, implement, verify, measure, keep/discard, log) does not. The process
   is what keeps you honest. The metric is what keeps you on track.

6. **The rationalizations table applies universally.** eARA's program.md includes a
   table of rationalizations that mean STOP. Every single one applies to software
   engineering:

   | Thought | Why it is wrong |
   |---|---|
   | "This change is simple enough that I do not need a reviewer." | Simple changes have caused the worst bugs. |
   | "I already read the codebase." | You read it in your context window. You have blind spots you cannot see. |
   | "The build passing will catch everything." | The build catches syntax errors. It does not catch logic errors, spec drift, or architectural violations. |
   | "These subagents are overkill for this change." | The protocol exists because previous agents thought the same thing and shipped broken code. |

### The bottom line

eARA is not an ML tool. It is a discipline framework for autonomous agents working
on modify-measure-decide loops. The training script becomes the source file. The
metric becomes the gate. The compute backend becomes the build system. The
experiment loop becomes the implementation cycle. The subagent verification stays
exactly what it is: an independent check by a fresh mind that has not been corrupted
by the implementing agent's assumptions.

The value of eARA for software engineering is not the loop (though loops have clear
applications in performance optimization, coverage improvement, and size reduction).
The value is the combination of:
- **Mandatory pre-checks** before every change
- **Mandatory subagent verification** after every change
- **Binary keep/discard** with no "keep with known issues"
- **Append-only logging** for accountability
- **Never stop, never ask** autonomy within the loop (when looping)

These principles apply to any domain where an autonomous agent modifies something,
measures the result, and decides whether to keep or discard the change. ML training
is one such domain. Software engineering is another. They are not the only two.

---

*This case study documents the RAMSpeed algorithmic improvements session (2026-03-24),
where an AI agent adapted eARA (eptesicuslabs/eARA) to implement 7 improvements to a
Windows memory optimizer's pipeline. 12 commits, 28 tests, 0 reverts, 14 subagent
dispatches.*

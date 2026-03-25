# eARA Gate Protocol

## Purpose

Gates are non-negotiable constraints that protect everything except the
primary metric. A gate failure means the experiment is discarded or fixed
in-place — there is no "keep with known gate failures." This document
defines how gates are checked, in what order, and what happens on failure.

---

## Gate Types

### Command Gates

Defined by a shell command that must exit 0 to pass.

```yaml
build:
  command: "dotnet build -o /tmp/build"
  required: true
```

The command is run as-is. Exit code 0 = pass. Any other exit code = fail.
Stdout/stderr are captured for diagnostic purposes.

### Subagent Gates

Defined by a subagent dispatch (not a command). The subagent reviews the
work and returns PASS or REJECT.

```yaml
spec_compliance:
  type: subagent
  required: true
```

Subagent gates follow `review-protocol.md`.

### Composite Gates

Some gates are composites of other checks:

- **test_before_ship**: Checks whether new public surface has corresponding
  tests. This is a judgment call by the agent, not a command.
- **post_merge_verification**: Runs all command gates from scratch after
  merging parallel work.
- **scope_gate**: Checks staged files against boundary definitions.
- **framing_gate**: Checks staged content for banned terms.

---

## Gate Checking Order

Gates are checked in this order. If a required gate fails, subsequent gates
are NOT checked (fail fast).

**Phase 1: Command gates (fast, automated)**

1. **build** — Can the code compile/build?
2. **lint** — Does the code pass lint rules? (if required)
3. **test** — Do all tests pass?
4. **no_regression** — Do pre-existing behaviors still work?
5. **test_before_ship** — Does new surface have tests? (if enabled)
6. **custom_gates** — In the order defined in the config.

**Phase 2: Review step (slow, dispatched per `review-protocol.md`)**

7. **spec_compliance** — Does an independent reviewer confirm spec match?
8. **code_quality** — Does an independent reviewer approve quality?

These are dispatched as a single REVIEW step per `review-protocol.md`,
NOT as independent gate runs. The `gates.spec_compliance` field in
`eara.yaml` controls whether spec review is required; the actual dispatch
happens through `review-protocol.md`. There is only ONE spec compliance
review per experiment — not a gate dispatch AND a review dispatch.

**Phase 3: Boundary and framing gates (commit-time checks)**

9. **scope_gate** — Are all files in the right project? (if enabled)
10. **framing_gate** — No banned terms in output? (if enabled)

**Rationale for order:** Fast, cheap command checks first (build takes
seconds). Subagent reviews second (take minutes — no point dispatching
if the build fails). Boundary and framing checks last (only at commit time).

---

## Gate Failure Handling

### Required gate fails

1. **In execution mode:**
   - If the fix is obvious and small: fix in-place, re-run the failed gate.
   - If the fix is non-trivial: DISCARD the entire experiment.
   - Do NOT proceed with a failed required gate.

2. **In loop mode:**
   - If `loop.behavior.pause_on_gate_failure` is false (default): DISCARD
     immediately. `git reset --hard` to last good commit. Continue to next
     iteration.
   - If `pause_on_gate_failure` is true: save state to `.eara-state.json`,
     PAUSE, wait for user. On resume, the failed experiment has been discarded.

3. **Never:**
   - Skip a required gate.
   - Mark an experiment as KEEP with a failed required gate.
   - Defer a gate failure to "fix later."

### Advisory gate fails (required: false)

1. Log the failure in the experiment notes.
2. The experiment is still eligible for KEEP.
3. The agent should consider fixing advisory issues if the fix is trivial.

---

## Post-Merge Verification Gate

**Enabled at:** ultra (or normal with override).

This gate is special — it runs AFTER merging parallel work, not after
a single experiment. It exists because worktree isolation creates a
stale-state problem: a subagent in a worktree does not see changes
made on the main branch.

### Trigger

After any of these events:
- Merging a worktree branch into main.
- Merging a feature branch into main.
- Rebasing onto a branch that has diverged.

### Procedure

1. Run `gates.build.command` from scratch. **Not incremental.** Clean build.
2. Run `gates.test.command`. **Full suite.** Not just changed files.
3. Run all other required command gates.
4. If any gate fails:
   - Diagnose the failure. It is likely caused by a conflict between the
     merged work and changes made on main since the worktree was created.
   - Fix the failure before proceeding to the next merge or next task.
   - **Do NOT proceed with a broken main branch.**

### Why this exists

The eMCP session dispatched 3 test-writing subagents in parallel worktrees.
When the worktrees merged, 2 tests failed because tool counts had changed
on main. The fix was trivial (update expected values), but the failure
would not have been caught without post-merge verification.

---

## Test-Before-Ship Gate

**Enabled at:** normal and ultra.

### Trigger

When an experiment introduces new public surface:
- New exported functions or methods.
- New API endpoints or routes.
- New CLI commands or flags.
- New tools (in MCP/plugin contexts).
- New public types or interfaces.

### Check

1. Does the experiment include tests that exercise the new surface?
2. If yes: gate passes.
3. If no: gate fails. The experiment is NOT eligible for KEEP.

### Resolution

The agent must either:
- Write tests as part of the same experiment (before KEEP).
- Dispatch a subagent to write tests.

Zero-test commits for new public surface are equivalent to untested
experiments. They do not count as KEEP.

### Why this exists

The eMCP session shipped 17 computer-use tools with zero tests. The security
gates could have been silently broken for the entire period between commit
and test creation. If `allowClick: false` had been ignored, nobody would
have known.

---

## Scope Gate (Boundary Enforcement)

**Enabled at:** ultra (or normal with override).

### Trigger

Before every commit, when `boundaries.scope_gate` is true.

### Check

For each staged file:
1. Does it match an `allowed_file_patterns` entry for the current project?
2. Does it match a `forbidden_file_patterns` entry?
3. If forbidden or if the file belongs to a different project: BLOCK.

At **ultra** with `cross_project_verification`:
- Also check that no artifact in the working directory has been placed in
  the wrong project root.

### Why this exists

The eSkill session committed CLAUDE.md (a Claude Code config file) and
marketplace.json (a plugin manifest) to a platform-agnostic skill library.
It also created 11 agent definitions in the skill repo instead of the
runtime repo.

---

## Framing Gate

**Enabled at:** normal and ultra (on correction), ultra (on every commit).

### On user correction (normal and ultra)

When the user corrects a project-level assumption:
1. HALT current work.
2. Search all files and outputs for the old framing.
3. Fix every instance.
4. Verify (search returns zero results).
5. Resume.

### On every commit (ultra)

When `framing.verify_framing_on_commit` is true:
1. Before committing, search all staged content for terms in
   `framing.project_is_not`.
2. If any banned term is found: BLOCK the commit.

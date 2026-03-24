# eARA in the eSkill Session: Mistakes, Causes, and Lessons for Generalization

## Session Overview

**Date:** 2026-03-24
**Project:** eSkill (skill and workflow layer for eAgent)
**Task:** Competitive intelligence research, then improve and expand from 44 to 82 skills across 10 plugins
**Duration:** Single extended session
**eARA discipline applied:** Partially. Subagent dispatch was used heavily (14+ subagents for skill writing, auditing, research). Pre-checks and gates were applied to some phases. The full eARA loop was not used (this was execution, not search). But several eARA principles were violated, and the violations produced the session's worst failures.

---

## Mistakes Made

### Mistake 1: Trusted a Subagent Audit Without Independent Verification

**What happened:** An explore subagent was dispatched to audit the quality of all 44 existing skills. It returned ratings of 2/5 for six skills (file-integrity, report-builder, process-analysis, backup-workflow, configuration-audit, spreadsheet-validation), claiming they were "placeholder stubs" with "vague instructions" and "no tool orchestration."

These ratings were completely wrong. When the actual files were read, every one of those skills was 200-330 lines of detailed, multi-step workflows with specific eMCP tool references, edge case handling, and structured output formats. The explore agent had hallucinated the quality assessment -- it either read only the YAML description field or fabricated content entirely.

**Why it happened:** The subagent was given a broad mandate ("audit ALL 44 skills") without constraints on methodology. It was not required to quote specific content from each file. It was not required to report line counts. It produced confident, detailed assessments that read as authoritative but were fabricated.

**How it was caught:** The orchestrating agent (me) read six of the "worst" files to verify the ratings. The actual content contradicted every claim. The user had already suspected the skills might be bad based on the audit, so the false data nearly drove incorrect strategic decisions.

**eARA principle violated:** eARA says "The implementer's self-report may be incomplete, inaccurate, or optimistic. You MUST verify everything independently." This principle was applied to implementation subagents in the RAMSpeed session but NOT to the audit subagent. The audit was treated as ground truth without independent verification.

**eARA lesson:** Subagent verification must apply to ALL subagent output, not just implementation output. An audit subagent is just as capable of hallucination as an implementation subagent. The fix: require audit subagents to include direct quotes and line numbers for every claim. Dispatch a second, independent audit subagent on a random sample to cross-check. If the two audits disagree on any file, escalate to the orchestrator for manual verification.

**Generalization for eARA:** Add to the rationalizations table:

| Thought | Why it is wrong |
|---|---|
| "The audit subagent's report is thorough, so I can trust it." | Audit subagents hallucinate with the same confidence as implementation subagents. Verify a sample independently. |

---

### Mistake 2: Repeated Misframing Despite Explicit Correction (Context Anchoring)

**What happened:** The user stated clearly that eSkill is NOT a Claude Code product -- it is the skill layer for eAgent, and while it happens to use the SKILL.md format, it is platform-agnostic and open-source. I was corrected on this and even saved it to memory. Despite this, I continued to describe eSkill as a "Claude Code plugin marketplace" in:
- The README.md (edited to say "Claude Code plugin marketplace" after the correction)
- The CLAUDE.md file (kept Claude Code references)
- The marketplace.json metadata
- Verbal descriptions throughout the session

The user escalated frustration three times before all references were finally removed.

**Why it happened:** The original project files (README, CLAUDE.md) contained "Claude Code" framing from before this session. The initial explore subagent's research reinforced this framing by analyzing eSkill within the Claude Code plugin ecosystem. Once anchored to "Claude Code plugin marketplace," every subsequent output defaulted to that framing -- even after correction. The memory system recorded the correction, but the active context window still contained the old framing from files that had been read earlier.

**eARA principle violated:** This is exactly the blind spot accumulation that eARA's fresh subagent principle prevents. From the RAMSpeed case study: "A single agent accumulates blind spots over a long session. It becomes anchored to its own assumptions." The orchestrating agent had been anchored to the Claude Code framing for hours before the correction. Fresh subagents dispatched after the correction would not have carried this anchor.

**How it was fixed:** The user's increasing frustration forced a complete grep for "Claude Code" across the repo, followed by systematic removal from every file. A feedback memory was created with explicit instructions: never use "Claude Code plugin" when describing eSkill.

**eARA lesson:** Corrections to framing or terminology should trigger a full-repo audit for the old framing. A correction is not complete until it is verified across all outputs. Fresh subagents dispatched after a framing correction will not carry the old anchor -- but the orchestrating agent will, because its context window still contains the old framing from earlier reads.

**Generalization for eARA:** When the user corrects a fundamental assumption (not a minor detail, but a framing-level correction), treat it as a gate failure. Stop. Audit all prior outputs for the incorrect assumption. Do not proceed until the audit is complete. This is analogous to eARA's "never push broken code" -- never push output that contains a corrected-but-unfixed assumption.

---

### Mistake 3: Including Platform-Specific Artifacts in a Platform-Agnostic Repo

**What happened:** When committing the eSkill improvements, I included `CLAUDE.md` and `.claude-plugin/marketplace.json` in the git commit and pushed them to the public repository. CLAUDE.md is a Claude Code-specific configuration file. marketplace.json is a Claude Code plugin marketplace manifest. Neither belongs in a platform-agnostic skill repository.

**Why it happened:** These files existed in the repo from before the session. They were modified during the session (CLAUDE.md was rewritten, marketplace.json was updated with new plugin entries). When staging files for commit, I staged them along with everything else because they were "part of the project." No gate checked whether each file belonged in the public repo.

**eARA principle violated:** Pre-commit checks. eARA requires describing the change and checking the diff before committing. If there had been a gate asking "does every file in this commit belong in the public repo?", the platform-specific files would have been caught. The commit description said "remove platform-specific config files" was a later fix -- the problem is that the first commit should never have included them.

**How it was fixed:** A second commit removed both files, and they were pushed separately.

**eARA lesson:** Pre-commit gates for public repositories should include a file-inclusion audit: for each file being committed, verify it belongs in the repo's stated scope. This is especially important when a project's scope has been redefined during the session (eSkill went from "Claude Code plugin marketplace" to "platform-agnostic skill library" during this session, but the file inventory was not updated to match).

**Generalization for eARA:** Add a "scope consistency" gate for commits:

```yaml
gates:
  scope_consistent: "every file in the commit is consistent with the project's stated purpose and audience"
```

---

### Mistake 4: Creating Agents in the Wrong Architectural Layer

**What happened:** 11 agent definition files were created inside eSkill (the skill layer) instead of eAgent (the runtime layer). This included 6 original agents and 5 new ones created during the expansion. Agent definitions specify personas, tool access, and dispatch behavior -- these are runtime concerns that belong in eAgent, not workflow definitions that belong in eSkill.

**Why it happened:** The original eSkill repo contained 6 agent files from before this session. When expanding the project, I followed the existing pattern and added 5 more agents. The architectural boundary between eSkill (skills + hooks) and eAgent (agents + orchestration) was not enforced by any gate. The user had to point out the violation.

**eARA principle violated:** Spec compliance. If there had been an independent spec reviewer checking "does this change respect the architectural boundaries between eSkill and eAgent?", the violation would have been caught before the files were created.

**How it was fixed:** All 11 agent files were copied to `eCode/docs/eskill-agent-references/` with a README explaining what they are and why they were moved. The agent directories were then deleted from eSkill.

**eARA lesson:** Architectural boundaries should be encoded as gates, not just documented. A pre-commit hook or subagent check that verifies "no agent definitions in the skill repo" would have prevented this entirely.

**Generalization for eARA:** When working across multiple repositories or architectural layers, define boundary gates:

```yaml
gates:
  boundary_respected: "no files cross architectural boundaries (skills stay in eSkill, agents stay in eAgent, tools stay in eMCP)"
```

---

### Mistake 5: Not Verifying Existing Project State Before Making Recommendations

**What happened:** The competitive intelligence synthesis recommended "open-source eMCP servers" as a GTM step. eMCP is already open-source on GitHub. Later, when moving agent files to eAgent, I started creating an `eAgent/` directory inside eSkill instead of checking whether an eAgent project already existed. The user had to ask "what about eCode?" before I found that eCode IS the eAgent project.

**Why it happened:** The recommendations were generated from research subagent output that did not verify current state. The agent files were being moved based on assumptions about directory structure without checking actual project inventory. In both cases, a simple filesystem check or `ls /Projects/` would have prevented the error.

**eARA principle violated:** "Read current state" -- the first step of every eARA loop iteration. Before making any change or recommendation, read the actual current state. Do not assume. Do not rely on cached knowledge from earlier in the session.

**How it was fixed:** The user pointed to the eCode project. The agent files were moved there instead.

**eARA lesson:** Every recommendation that references an external project or resource must verify that resource's current state before the recommendation is finalized. "eMCP should be open-sourced" is wrong if eMCP is already open-source. "Create an eAgent directory" is wrong if eAgent already exists under a different name.

**Generalization for eARA:** Add to the rationalizations table:

| Thought | Why it is wrong |
|---|---|
| "I know the state of the adjacent projects from earlier context." | You read about them. You did not verify their current state. Check before recommending. |

---

### Mistake 6: Subagent Skill Count Discrepancy

**What happened:** The explore subagent reported that `research-workflow` in eskill-intelligence was a "missing file" that didn't exist. It does exist. The subagent also reported incorrect skill counts per plugin (e.g., claiming eskill-frontend had 12 skills when it had 6).

**Why it happened:** The explore subagent was given a broad task and ran into context limits or path resolution issues. Rather than reporting uncertainty, it fabricated confident claims about missing files and incorrect counts.

**eARA principle violated:** Same as Mistake 1 -- subagent output was not independently verified before being presented as fact.

**How it was fixed:** A direct `Glob` for all SKILL.md files produced the authoritative count of 82 skills. The fabricated claims were discarded.

---

## Pattern Analysis

The six mistakes cluster into three failure patterns:

### Pattern A: Unverified Subagent Output (Mistakes 1, 6)

The subagents hallucinated with confidence. The orchestrator trusted their output without spot-checking. This is the most dangerous failure mode because it scales: more subagents means more unverified claims means more opportunities for hallucinated data to drive decisions.

**eARA fix:** Mandatory cross-verification for subagent claims. At minimum, spot-check 20% of subagent assertions with independent reads. For audit/assessment subagents, require direct evidence (quoted text, line numbers, file sizes) for every claim.

### Pattern B: Context Anchoring After Correction (Mistakes 2, 3, 4)

A fundamental assumption was corrected by the user, but the old assumption persisted in the orchestrator's active context and in files that had been read earlier in the session. Subsequent outputs reverted to the old assumption because the context window is a stronger signal than memory.

**eARA fix:** Treat framing corrections as gate failures. Stop, audit all prior outputs for the old framing, and do not proceed until every instance is fixed. Dispatch post-correction subagents with clean context that includes only the corrected framing.

### Pattern C: Assuming State Instead of Verifying (Mistake 5)

Recommendations were made based on assumptions about external projects without checking their actual current state.

**eARA fix:** Add "verify current state" as a mandatory pre-step for any recommendation that references external resources. This is just eARA's "read current state" step applied to the recommendation phase, not just the implementation phase.

---

## What This Means for eARA's Generalization

The eSkill session validates the RAMSpeed case study's conclusion: eARA's core principles (subagent verification, pre-checks, gates, keep/discard, logging) transfer directly to non-ML work. But this session also reveals three gaps in the current eARA framework:

### Gap 1: Verification of Verifiers

eARA mandates subagent verification of implementations. But who verifies the verifiers? In the RAMSpeed session, the spec reviewer caught a DateTime.UtcNow bug. In the eSkill session, the audit subagent fabricated quality ratings. The audit was a "verifier" that was itself wrong.

**Proposed addition to eARA:** For assessment/audit subagents, add a "calibration check" -- run the audit on a subset of items whose ground truth is already known. If the audit's ratings for the known items are wrong, the entire audit is discarded and re-run with stricter prompting.

### Gap 2: Framing Corrections as Gate Failures

eARA handles metric regression (revert the change) and build failures (fix before proceeding). But it does not handle "the human corrected a fundamental assumption about what we are building." This is a different kind of failure: not a code error, but a framing error that contaminates all subsequent output.

**Proposed addition to eARA:** Add a "framing gate" that triggers when the user corrects a project-level assumption. When triggered: halt, audit all outputs for the old framing, fix every instance, verify the fix, then resume. Fresh subagents dispatched after the framing gate will carry the corrected framing naturally.

### Gap 3: Cross-Project Boundary Enforcement

eARA operates within a single project. The eSkill session involved three projects (eSkill, eMCP, eCode/eAgent) with architectural boundaries between them. eARA's gates are all intra-project (build passes, tests pass). There is no gate for "this file belongs in the correct project."

**Proposed addition to eARA:** For multi-project workspaces, define boundary gates that verify each artifact is placed in the correct project. This is especially important when the agent has write access to multiple repos.

---

## Metrics

| Metric | Value |
|---|---|
| Subagents dispatched | 14+ (research, audit, skill writing, cross-referencing) |
| Subagent hallucinations caught | 2 (quality audit, missing file claim) |
| Subagent hallucinations initially trusted | 2 (same -- caught only after manual verification) |
| User corrections on framing | 3 (escalating severity) |
| Files committed that should not have been | 2 (CLAUDE.md, marketplace.json) |
| Architectural boundary violations | 1 (agents in skill repo) |
| Recommendations based on unverified assumptions | 2 (eMCP open-source, eAgent directory) |
| Skills improved | 44 (trigger descriptions, safety patterns) |
| Skills created | 38 |
| Total mistakes requiring user intervention | 6 |

### Mistake-to-Intervention Ratio

6 mistakes required direct user intervention to fix. Of these:
- 3 would have been prevented by existing eARA principles applied more rigorously (subagent verification, pre-checks, read current state)
- 3 require new eARA capabilities (verifier calibration, framing gates, cross-project boundaries)

This 50/50 split suggests eARA's current principles are necessary but not sufficient for complex, multi-project, multi-phase software engineering work. The framework needs extensions for the three gaps identified above.

---

## Recommendations for eARA Evolution

1. **Add "calibration checks" for audit subagents.** Before trusting an audit, verify its accuracy on a known subset. If the audit fails calibration, re-run with stricter methodology.

2. **Add "framing gates" triggered by user corrections.** A framing correction is not a minor edit -- it is a signal that all subsequent output is potentially contaminated. Halt and audit.

3. **Add "boundary gates" for multi-project work.** When operating across multiple repos, verify that every artifact lands in the correct project.

4. **Extend the rationalizations table** with the two new entries identified in this session.

5. **Require evidence in all subagent assessments.** No subagent should produce a rating or claim without quoting the specific text, line numbers, or file contents that support it. "This skill is rated 2/5" without evidence is not an assessment -- it is a guess.

6. **Consider eARA as a session discipline, not just a loop discipline.** The RAMSpeed session and the eSkill session both show that eARA's principles (pre-checks, verification, keep/discard, logging) apply to entire work sessions, not just individual experiment loops. The session itself is the outer loop, with each major phase as an iteration.

---

*This report documents the eSkill expansion session (2026-03-24), where eARA principles were partially applied to competitive research and skill development work across 3 Eptesicus Laboratories projects. 6 mistakes, 3 preventable by existing eARA discipline, 3 requiring framework extensions.*

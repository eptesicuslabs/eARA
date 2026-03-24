#!/usr/bin/env python3
"""eARA self-test: validates the eARA v1.0 implementation."""

import yaml
import os
import sys
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
ERRORS = []
WARNINGS = []

def error(msg):
    ERRORS.append(msg)
    print(f"  FAIL: {msg}")

def warn(msg):
    WARNINGS.append(msg)
    print(f"  WARN: {msg}")

def ok(msg):
    print(f"  PASS: {msg}")

# ─── Gate 1: All YAML files parse cleanly ─────────────────────────

print("\n=== Gate 1: YAML Parsing ===")
yaml_files = list(ROOT.glob("spec/*.yaml")) + list(ROOT.glob("examples/*.yaml")) + [ROOT / "eara.yaml"]
for f in yaml_files:
    try:
        with open(f) as fh:
            yaml.safe_load(fh)
        ok(f"  {f.name} parses cleanly")
    except Exception as e:
        error(f"  {f.name} failed to parse: {e}")

# ─── Gate 2: Schema has required top-level fields ─────────────────

print("\n=== Gate 2: Schema Structure ===")
with open(ROOT / "spec/eara.schema.yaml") as f:
    schema = yaml.safe_load(f)

required_fields = ["eara_version", "project", "strictness", "mode"]
schema_required = schema.get("required", [])
for field in required_fields:
    if field in schema_required:
        ok(f"Schema requires '{field}'")
    else:
        error(f"Schema missing required field '{field}'")

schema_props = schema.get("properties", {})
expected_props = ["eara_version", "project", "description", "strictness", "mode",
                  "metric", "gates", "review", "loop", "logging", "boundaries",
                  "framing", "source_files"]
for prop in expected_props:
    if prop in schema_props:
        ok(f"Schema defines property '{prop}'")
    else:
        error(f"Schema missing property '{prop}'")

# Check conditional requirement for loop mode
if "if" in schema:
    ok("Schema has conditional requirements (if/then)")
else:
    error("Schema missing conditional requirements for loop mode")

# ─── Gate 3: Strictness profiles are complete ─────────────────────

print("\n=== Gate 3: Strictness Profiles ===")
with open(ROOT / "spec/strictness-profiles.yaml") as f:
    profiles_doc = yaml.safe_load(f)

profiles = profiles_doc.get("profiles", {})
expected_profiles = ["minimal", "standard", "strict", "paranoid"]
for name in expected_profiles:
    if name in profiles:
        ok(f"Profile '{name}' defined")
        # Check that each profile has the expected sections
        profile = profiles[name]
        for section in ["gates", "review", "logging", "boundaries", "framing"]:
            if section in profile:
                ok(f"  '{name}' has '{section}' section")
            else:
                error(f"  '{name}' missing '{section}' section")
    else:
        error(f"Profile '{name}' not defined")

# Verify strict+ has post_merge_verification enabled
strict_pmv = profiles.get("strict", {}).get("gates", {}).get("post_merge_verification", {}).get("enabled", False)
paranoid_pmv = profiles.get("paranoid", {}).get("gates", {}).get("post_merge_verification", {}).get("enabled", False)
if strict_pmv:
    ok("strict profile has post_merge_verification enabled")
else:
    error("strict profile missing post_merge_verification")
if paranoid_pmv:
    ok("paranoid profile has post_merge_verification enabled")
else:
    error("paranoid profile missing post_merge_verification")

# Verify standard+ has test_before_ship enabled
for pname in ["standard", "strict", "paranoid"]:
    tbs = profiles.get(pname, {}).get("gates", {}).get("test_before_ship", {}).get("enabled", False)
    if tbs:
        ok(f"{pname} profile has test_before_ship enabled")
    else:
        error(f"{pname} profile missing test_before_ship")

# Verify paranoid has evidence requirements
paranoid_ev = profiles.get("paranoid", {}).get("review", {}).get("evidence_requirements", {})
for req in ["require_quotes", "require_line_numbers", "require_file_sizes"]:
    if paranoid_ev.get(req, False):
        ok(f"paranoid has {req} enabled")
    else:
        error(f"paranoid missing {req}")

# ─── Gate 4: Rationalizations count ──────────────────────────────

print("\n=== Gate 4: Rationalizations ===")
with open(ROOT / "spec/rationalizations.yaml") as f:
    rat_doc = yaml.safe_load(f)

rats = rat_doc.get("rationalizations", [])
if len(rats) == 14:
    ok(f"Rationalizations table has {len(rats)} entries (expected 14)")
else:
    error(f"Rationalizations table has {len(rats)} entries (expected 14)")

# Check IDs are sequential R01-R13
for i, rat in enumerate(rats):
    expected_id = f"R{i+1:02d}"
    actual_id = rat.get("id", "")
    if actual_id == expected_id:
        ok(f"  {expected_id}: '{rat.get('thought', '')[:50]}...'")
    else:
        error(f"  Expected {expected_id}, got {actual_id}")

# Check each has required fields
for rat in rats:
    for field in ["id", "thought", "why_wrong", "source", "applies_at"]:
        if field not in rat:
            error(f"  Rationalization {rat.get('id', '?')} missing field '{field}'")

# ─── Gate 5: Results schema ──────────────────────────────────────

print("\n=== Gate 5: Results Schema ===")
with open(ROOT / "spec/results-schema.yaml") as f:
    results_doc = yaml.safe_load(f)

columns = results_doc.get("columns", [])
expected_columns = ["timestamp", "experiment_id", "agent_type", "status",
                    "metric_before", "metric_after", "gates_status",
                    "commit_hash", "description", "review_findings",
                    "duration_seconds"]
actual_names = [c["name"] for c in columns]
for col in expected_columns:
    if col in actual_names:
        ok(f"Results schema has column '{col}'")
    else:
        error(f"Results schema missing column '{col}'")

# Check agent_type includes orchestrator
agent_type_col = next((c for c in columns if c["name"] == "agent_type"), None)
if agent_type_col and "orchestrator" in agent_type_col.get("enum", []):
    ok("Results schema agent_type includes 'orchestrator'")
else:
    error("Results schema agent_type missing 'orchestrator'")

# ─── Gate 6: Cross-reference integrity ───────────────────────────

print("\n=== Gate 6: Cross-References ===")
protocol_files = list(ROOT.glob("protocol/*.md"))
all_refs = []
for pf in protocol_files:
    content = pf.read_text()
    # Find references like `protocol/foo.md`, `spec/bar.yaml`, or bare `foo.md`
    # Full-path refs (protocol/, spec/, examples/)
    full_refs = re.findall(r'`((?:protocol|spec|examples)/[^`]+)`', content)
    for ref in full_refs:
        target = ROOT / ref
        if target.exists():
            ok(f"  {pf.name} → {ref} exists")
        else:
            error(f"  {pf.name} → {ref} MISSING")
        all_refs.append((pf.name, ref))
    # Bare same-directory refs (e.g., `gate-protocol.md` from within protocol/)
    bare_refs = re.findall(r'`([a-z][\w-]+\.(?:md|yaml))`', content)
    for ref in bare_refs:
        # Resolve relative to the file's own directory
        target = pf.parent / ref
        if target.exists():
            ok(f"  {pf.name} → {ref} exists (same-dir)")
        else:
            # Also check from root
            if not (ROOT / ref).exists():
                error(f"  {pf.name} → {ref} MISSING")
        all_refs.append((pf.name, ref))

# Check that gate-protocol.md and logging-protocol.md are referenced
gate_refs = [r for r in all_refs if "gate-protocol" in r[1]]
logging_refs = [r for r in all_refs if "logging-protocol" in r[1]]
if gate_refs:
    ok(f"gate-protocol.md is referenced by {len(gate_refs)} document(s)")
else:
    error("gate-protocol.md is not referenced by any document")
if logging_refs:
    ok(f"logging-protocol.md is referenced by {len(logging_refs)} document(s)")
else:
    error("logging-protocol.md is not referenced by any document")

# ─── Gate 7: Example configs match schema structure ───────────────

print("\n=== Gate 7: Example Config Validation ===")
example_files = list(ROOT.glob("examples/eara-*.yaml"))
# Exclude the legacy file
example_files = [f for f in example_files if "legacy" not in f.name]

for ef in example_files:
    with open(ef) as f:
        config = yaml.safe_load(f)

    # Check required fields
    has_version = config.get("eara_version") == "1.0"
    has_project = "project" in config
    has_strictness = "strictness" in config
    has_mode = "mode" in config

    if has_version and has_project and has_strictness and has_mode:
        ok(f"  {ef.name}: all required fields present")
    else:
        missing = []
        if not has_version: missing.append("eara_version")
        if not has_project: missing.append("project")
        if not has_strictness: missing.append("strictness")
        if not has_mode: missing.append("mode")
        error(f"  {ef.name}: missing {', '.join(missing)}")

    # If loop mode, check metric and loop are present
    if config.get("mode") == "loop":
        if "metric" in config:
            ok(f"  {ef.name}: loop mode has 'metric'")
        else:
            error(f"  {ef.name}: loop mode missing 'metric'")
        if "loop" in config:
            ok(f"  {ef.name}: loop mode has 'loop' config")
        else:
            error(f"  {ef.name}: loop mode missing 'loop' config")

# ─── Gate 8: program.md covers all sections ──────────────────────

print("\n=== Gate 8: program.md Completeness ===")
program = (ROOT / "program.md").read_text()

required_sections = [
    ("Bootstrap", r"## 1\. Bootstrap"),
    ("Execution Protocol", r"## 2\. Execution Protocol"),
    ("Loop Protocol", r"## 3\. Loop Protocol"),
    ("Strictness Profiles", r"## 4\. Strictness Profiles"),
    ("Review Protocol", r"## 5\. Review Protocol"),
    ("Logging", r"## 6\. Logging"),
    ("Rationalizations", r"## 7\. Rationalizations"),
    ("Gates", r"## 8\. Gates"),
    ("Boundaries", r"## 9\. Boundaries"),
    ("Binary Decision", r"## 10\. The Binary Decision"),
]

for name, pattern in required_sections:
    if re.search(pattern, program):
        ok(f"  program.md has section: {name}")
    else:
        error(f"  program.md missing section: {name}")

# Check rationalizations table in program.md has 13 entries
rat_rows = re.findall(r'\| R\d{2} \|', program)
if len(rat_rows) == 14:
    ok(f"  program.md rationalizations table has {len(rat_rows)} entries")
else:
    error(f"  program.md rationalizations table has {len(rat_rows)} entries (expected 14)")

# ─── Summary ─────────────────────────────────────────────────────

print(f"\n{'='*60}")
print(f"RESULTS: {len(ERRORS)} errors, {len(WARNINGS)} warnings")
print(f"{'='*60}")

if ERRORS:
    print("\nFAILED GATES:")
    for e in ERRORS:
        print(f"  ✗ {e}")
    sys.exit(1)
else:
    print("\nALL GATES PASSED")
    sys.exit(0)

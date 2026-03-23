# eARA

Eptesicus Autonomous Research Agent.

Give an AI agent `program.md` and a training script. It modifies the code,
trains, checks if the result improved, keeps or discards, and repeats.
You come back to a log of experiments and a better model.

Inspired by [karpathy/autoresearch](https://github.com/karpathy/autoresearch),
adapted for remote GPU backends (Kaggle, RunPod) and configurable experiment
gates.

## How it works

Two files:

- **`program.md`** -- universal agent instructions. The agent reads this and
  runs the experiment loop autonomously. Works with any LLM agent (Claude Code,
  Codex, Gemini, etc).
- **`eara.yaml`** -- project-specific config. Points to your training script,
  defines the metric to optimize, compute backend, and pass/fail gates.

No framework code. No Python package. The agent IS the framework.

## Quick start

1. Copy `program.md` and `eara.yaml` into your project root.
2. Edit `eara.yaml` to point to your training script and configure your
   compute backend.
3. Point your agent at the repo and say: "read program.md and start experimenting."

## Compute backends

### Local GPU

```yaml
compute: "local"
local:
  command: "python train.py"
  log_file: "run.log"
  results_file: "results.json"
```

### Kaggle (free T4)

```yaml
compute: "kaggle"
kaggle:
  kernel_ref: "username/kernel-name"
  notebook_dir: "notebooks/autoresearch"
  output_dir: "notebooks/autoresearch/output"
  accelerator: "NvidiaTeslaT4"
  api_token_env: "KAGGLE_API_TOKEN"
```

### RunPod

```yaml
compute: "runpod"
runpod:
  api_key_env: "RUNPOD_API_KEY"
  gpu_type: "NVIDIA RTX 4090"
  docker_image: "runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04"
  script_path: "train.py"
  results_file: "results.json"
```

## The loop

```
LOOP FOREVER:
  1. Read state (results.tsv, gates)
  2. Decide what to try
  3. Modify train script
  4. Pre-run checks (describe, crash-check, smoke test, commit)
  5. Launch training (local / kaggle / runpod)
  6. Wait for completion
  7. Read results
  8. Log to results.tsv
  9. Keep (if improved) or revert (if worse)
  10. Post-run analysis (compare, gates, anomalies, docs)
  11. Repeat
```

The agent runs until you interrupt it.

## Project structure

```
program.md      -- agent instructions (universal)
eara.yaml       -- project config (project-specific)
results.tsv     -- experiment log (created by agent)
train.py        -- your training script (modified by agent)
```

## Design principles

- One file to modify. The agent only touches the training script.
- One metric to optimize. Defined in eara.yaml.
- The agent never stops. It runs until interrupted.
- Simple over complex. Removing code for equal results is a win.
- Never push broken code. Pre-run checks are mandatory.

Eptesicus Laboratories.

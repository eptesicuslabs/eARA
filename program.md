# eARA

Eptesicus Autonomous Research Agent. Universal experiment loop for ML research.

Give an agent this file and a training script. It modifies the code, trains,
checks if the result improved, keeps or discards, and repeats. You come back
to a log of experiments and a better model.

## Setup

To set up a new experiment session:

1. **Read the config**: Open `eara.yaml` in the project root. It defines:
   - `train_script`: path to the training script you will modify
   - `train_command`: how to launch training (local, Kaggle, or RunPod)
   - `metric`: the key metric to optimize (e.g. `val_bpb`, `val_loss`, `accuracy`)
   - `metric_direction`: `lower` or `higher` (is lower better, or higher?)
   - `gates`: optional pass/fail conditions beyond the main metric
   - `time_budget_minutes`: max training time per experiment
   - `knowledge_dir`: path to accumulated research notes (optional)
   - `docs_dir`: path to documentation to keep updated (optional)
2. **Read the training script**: Understand the model, optimizer, data, and metrics.
3. **Read state**: Check `results.tsv` for prior experiments. Check `eara.yaml` for current goals.
4. **Verify compute works**: Run the train command once to confirm. For remote backends (Kaggle/RunPod), verify auth.
5. **Confirm and go**.

## eara.yaml

```yaml
# --- Required ---
train_script: "train.py"                    # the file you modify
metric: "val_bpb"                           # key from results output
metric_direction: "lower"                   # "lower" or "higher"

# --- Compute backend (pick one) ---
compute: "local"                            # "local", "kaggle", or "runpod"

# Local GPU
local:
  command: "python train.py"                # how to run training
  log_file: "run.log"                       # where stdout/stderr goes
  results_file: "results.json"              # where metrics are written

# Kaggle
kaggle:
  kernel_ref: "username/kernel-name"
  notebook_dir: "notebooks/autoresearch"
  output_dir: "notebooks/autoresearch/output"
  accelerator: "NvidiaTeslaT4"              # or "NvidiaTeslaP100", etc
  api_token_env: "KAGGLE_API_TOKEN"

# RunPod
runpod:
  api_key_env: "RUNPOD_API_KEY"
  gpu_type: "NVIDIA RTX 4090"
  docker_image: "runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04"
  volume_id: ""                             # persistent storage ID
  script_path: "train.py"
  results_file: "results.json"

# --- Optional ---
time_budget_minutes: 30                     # max wall time per experiment
gates: {}                                   # named pass/fail conditions
knowledge_dir: ""                           # path to research notes
docs_dir: ""                                # path to docs to update
state_dir: "."                              # where results.tsv lives
```

## Compute backends

### Local GPU

Simplest. Run the command, wait, read the log.

```
Launch:  {local.command} > {local.log_file} 2>&1
Check:   grep "^{metric}:" {local.log_file}
Results: cat {local.results_file}
```

### Kaggle

Remote GPU via Kaggle API. Push notebook, poll, pull.

```
Push:    api.kernels_push(notebook_dir, acc=accelerator)
Poll:    loop: api.kernels_status(kernel_ref) until COMPLETE/ERROR
Pull:    api.kernels_output(kernel_ref, output_dir)
Results: output_dir/results.json
Web UI:  https://www.kaggle.com/code/{kernel_ref}
```

Auth: set the env var named in `kaggle.api_token_env` before running.
The kaggle package auto-authenticates on import -- the env var MUST be set
before any `from kaggle...` import.

### RunPod

Remote GPU via RunPod serverless or pods.

```
Create:  runpod.create_pod(gpu_type, docker_image, volume_id)
Upload:  rsync/scp the training script to the pod
Run:     ssh pod "python {script_path}"
Pull:    scp pod:{results_file} .
Destroy: runpod.terminate_pod(pod_id)
Results: {results_file}
```

Auth: set the env var named in `runpod.api_key_env`.

## Experimentation

**What you CAN do:**
- Modify the file at `train_script`. Everything is fair game: architecture,
  optimizer, hyperparameters, training loop, batch size, model size, schedule.

**What you CANNOT do:**
- Modify files outside `train_script` during the experiment loop.
- Install packages not available in the compute environment.
- Skip the pre-push checks.

**The goal: optimize `metric` AND pass all `gates`.**

## Pre-run checks

Before EVERY training launch:

1. **Describe**: What are you changing? Why? What do you expect?
2. **Crash-check**: Read through your diff. Trace tensor shapes. Check
   serialization. Check memory at configured batch size and sequence length.
3. **Smoke test**: Run a minimal forward pass locally (CPU, 2 steps, tiny config).
   Must complete in 30 seconds. Verify shapes, no crashes, correct output format.
4. **Commit**: `git add {train_script} && git commit -m "description"`

If ANY check fails, fix before launching. Never send broken code to remote GPU.

## Output format

The training script must write a JSON file (at `results_file`) containing
at minimum the key named in `metric`. Example:

```json
{
  "val_bpb": 2.8186,
  "training_time": 7862.39,
  "peak_memory_mb": 12400
}
```

For local runs, the script can also print key=value pairs to stdout:

```
val_bpb:          2.818600
training_seconds: 7862.4
peak_vram_mb:     12400.0
```

## Logging results

Log every experiment to `results.tsv` (tab-separated).

Header and columns:

```
commit	metric_value	time_min	status	description
```

1. git commit hash (7 chars)
2. metric value -- use 0.000000 for crashes
3. wall time in minutes -- use 0.0 for crashes
4. status: `keep`, `discard`, or `crash`
5. short description of what was tried

Example:

```
commit	metric_value	time_min	status	description
a1b2c3d	2.881300	27.0	keep	baseline 500 steps
b2c3d4e	2.818600	262.0	keep	progressive training 256->2048
c3d4e5f	0.000000	0.0	crash	doubled batch size (OOM)
d4e5f6g	2.950000	28.0	discard	removed layer norm (regression)
```

## Post-run analysis

After every completed run:

1. **Compare to best**: Is the metric better? Check `results.tsv`.
2. **Check gates**: If `gates` are defined in `eara.yaml`, evaluate them against
   the results. Log pass/fail.
3. **Check for anomalies**: Did anything regress by more than 10%? Did training
   time change dramatically? Any NaN or unexpected values?
4. **Update docs**: If `docs_dir` is set, update experiment logs and status files.
5. **Search for explanations**: If anything unexpected happened, search the web
   or read `knowledge_dir` files for prior findings.

## The experiment loop

LOOP FOREVER:

1. Read current state: `results.tsv`, `eara.yaml`, any gate definitions.
2. Decide what to try. Consider:
   - Current best metric value
   - Which gates are failing (if any)
   - What the knowledge files suggest (if any)
   - What has already been tried (check results.tsv)
3. Modify `{train_script}` with the experimental idea.
4. Run pre-run checks (describe, crash-check, smoke test, commit).
5. Launch training:
   - **local**: `{command} > {log_file} 2>&1` and wait
   - **kaggle**: push, poll until done, pull
   - **runpod**: create pod, upload, run, pull, destroy
6. Read results from the output file.
7. If crashed: read the log/traceback. Fix if trivial, otherwise log as crash.
8. Log to `results.tsv`.
9. If metric improved: keep the commit (advance the branch).
10. If metric is worse or equal: `git reset --hard HEAD~1` (revert).
11. Run post-run analysis.
12. Go to step 1.

## Rules

- **NEVER STOP.** Once the loop begins, do not pause to ask the human anything.
  The human may be asleep. You are autonomous. If you run out of ideas, think
  harder -- read knowledge files, re-read the training script, try combining
  previous near-misses, try radical changes. The loop runs until the human
  interrupts you.
- **Never launch without pre-run checks passing.**
- **Never queue multiple remote runs.** One at a time. Wait for completion.
- **Always log to results.tsv** after every experiment, including crashes.
- **Always update docs** (if docs_dir is configured) after every run.
- **Always search for explanations** when something unexpected happens.
- **Keep it simple.** A small improvement that adds complexity is not worth it.
  Removing something and getting equal results is a win.

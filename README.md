# eara

eptesicus autonomous research agent. give an ai agent a training script and
let it experiment autonomously. it modifies the code, trains, checks if the
result improved, keeps or discards, and repeats. you come back to a log of
experiments and a better model.

inspired by [karpathy/autoresearch](https://github.com/karpathy/autoresearch),
extended with remote gpu backends (kaggle, runpod) and configurable pass/fail
gates beyond a single metric.

## how it works

two files. no framework code. no python package. the agent is the framework.

program.md contains universal agent instructions. the agent reads it and runs
the experiment loop autonomously. works with any llm agent -- claude code,
codex, gemini, or anything that can read files, edit code, and run commands.

eara.yaml is the project-specific config. it points to your training script,
defines the metric to optimize, the compute backend, and optional pass/fail
gates.

copy both files into your project root, edit eara.yaml, point your agent at
the repo, and say "read program.md and start experimenting."

## compute backends

local gpu -- run the training command directly, wait, read results.

kaggle -- push a notebook to kaggle via the api, poll until complete, pull
results. free t4 gpu, 30 hours per week. set the kaggle_api_token env var.

runpod -- create a pod via the api, upload the script, run, pull results,
destroy the pod. any gpu type available. set the runpod_api_key env var.

all three backends follow the same interface: launch, wait, read results.
switching between them is a one-line change in eara.yaml.

## the loop

the agent runs this loop until interrupted:

1. read current state (results.tsv history, gate definitions)
2. decide what to try based on prior results and available knowledge
3. modify the training script with the experimental idea
4. pre-run checks: describe the change, trace tensor shapes for crashes,
   run a 30-second local smoke test, git commit
5. launch training on the configured compute backend
6. wait for completion (blocking, no polling noise)
7. read results from the output file
8. log to results.tsv
9. if the metric improved, keep the commit and advance the branch
10. if worse or equal, git reset to revert
11. post-run analysis: compare to prior best, check gates, investigate anomalies
12. repeat from step 1

the agent never stops. it never asks for permission. if it runs out of ideas
it reads the knowledge files, re-reads the training script, combines previous
near-misses, or tries radical changes. the loop runs until the human
interrupts it.

## gates

beyond the primary metric, eara.yaml can define named pass/fail conditions.
these are checked after every run. examples: spike firing rate must stay in
30-60%, perplexity must not degrade more than 20% during context extension,
memory must stay under a budget. gates prevent the agent from optimizing the
metric at the expense of other properties.

## design principles

one file to modify. the agent only touches the training script.

one metric to optimize. defined in eara.yaml.

simple over complex. a small improvement that adds ugly complexity is not
worth it. removing something and getting equal results is a win.

never push broken code. pre-run checks are mandatory before every training
launch, especially on remote gpu where a crash wastes 30+ minutes.

## for agents

if you are an ai agent reading this repo, here is what you need to know:

read program.md first. it contains the complete protocol for running
experiments autonomously. read eara.yaml to understand the project-specific
configuration: what file to modify, what metric to optimize, which compute
backend to use, and what gates must pass.

the training script is the only file you modify during the experiment loop.
everything else is read-only. results.tsv is the append-only log of all
experiments -- read it to understand what has been tried before and what the
current best metric value is.

your job is to lower the metric (or raise it, depending on metric_direction
in eara.yaml) while keeping all gates passing. you have full autonomy. do
not ask the human for permission. do not stop unless the human interrupts
you. if something crashes, fix it or skip it and move on.

pre-run checks are not optional. before every training launch: describe your
change in the commit message, check for shape mismatches and serialization
bugs, run a local smoke test (2 steps on cpu, 30 seconds max), and commit.
only then push to the compute backend.

after every run: compare to the best result in results.tsv, check all gates,
update documentation if a docs_dir is configured, and search for explanations
if anything unexpected happened. then decide the next experiment and continue.

eptesicus laboratories.

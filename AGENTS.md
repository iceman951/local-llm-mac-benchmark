# Agent instructions

## Start here

1. Read [docs/HANDOFF.md](docs/HANDOFF.md) for the latest completed work,
   pending work, run IDs and known caveats.
2. Read `README.md` and `docs/methodology.md` before starting an experiment.
   Consult `docs/metrics.md` and `docs/metadata.md` before changing analysis.
3. Inspect `git status --short`, `results/summary/results.csv` and relevant
   `metadata/runs/*.json`. Preserve user changes and existing results.
4. Check for an existing run before launching another. A handoff is a snapshot;
   verify live process/container state and recent logs. Do not launch duplicate
   runs because a previous agent's tool session ID is unavailable.

## Project and user intent

This repository benchmarks local coding assistants on an Apple Silicon Mac,
using native Ollama inference and the pinned Aider Polyglot harness in Docker.
Keep configurations, raw outputs, metadata and summaries in this repository.
Communicate with the user in Thai; repository documentation is in English.

The user authorized choosing and downloading a suitable local model when they
ask to run the next model. Proceed with necessary preparation and the requested
run without repeatedly asking for confirmation. This is not a request for an
unbounded model sweep or full-suite run. A documentation-only request does not
start another benchmark. Follow the latest user instruction and pending work
in the handoff; do not treat an unselected model as an already queued experiment.

## Experiment rules

- Execute generated code and exercise tests only inside the benchmark Docker
  container. Never execute files under `results/raw/` directly on the host.
- Use the existing scripts and pinned source checkouts. Do not weaken Docker
  isolation, mount the home directory/Docker socket, or pass API secrets.
- Keep inference local. Do not substitute cloud models or paid APIs.
- Start new models with three tasks, one worker, two attempts, whole-file edits,
  context 8192 and requested temperature 0 unless the user specifies otherwise.
- For comparisons, replay the saved manifest from the first run:
  `results/raw/20261003T035503Z-smoke-ae34538d/tasks.json`.
  It fixes both the tasks and their order. Do not replace hard tasks to improve
  scores. Larger task counts require an intentional new manifest/configuration.
- Do not manually repair model solutions, edit tests or overwrite old results.
  Each new attempt at an experiment gets a fresh run directory from the runner.
- Reuse the existing image when valid. Rebuilding can change mutable upstream
  packages even with identical source pins; record a changed image as a new
  experimental condition.
- Configuration files are parsed `KEY=VALUE`, not shell scripts: never source
  them. Environment variables override the selected file. Record actual settings.
- Preserve unknown/incomplete outcomes as unknown. A completed runner with zero
  passed tasks is a valid recorded outcome, not a reason to discard the run.
- Review raw test output before attributing failures to the model: missing
  toolchains, network failures and timeouts can also cause failed tests.
- Three tasks do not support general model rankings. Memory/swap metrics are
  whole-host samples, not model-only use. Do not infer energy use while on AC.
- Tokens/sec, temperature and watts are unsupported summary metrics. Do not
  fill them with estimates or ad hoc log-derived values.

## Running and monitoring

Before a requested run, inspect `ollama list`, `ollama ps`, `docker ps`,
`pmset -g batt`, `sysctl -n vm.swapusage` and available disk space. Check model
size against the shared 24 GiB memory budget, Docker and background applications.
Do not close unrelated apps, stop unrelated containers or evict unrelated models.
Record baseline swap, power source, model residency and uncontrolled conditions.

Use a distinct, non-secret `configs/<model>-smoke.env` file. Copy the existing
`configs/qwen35-9b-smoke.env` as a starting point and change `MODEL_NAME` and
`RUN_LABEL`; preserve the task manifest and controls for a comparable smoke run.
Verify the exact local identifier with `ollama list`. If a download is needed,
check the official model listing and retain the pull log.

Run these commands with the selected config path substituted:

```bash
BENCHMARK_CONFIG=configs/<model>-smoke.env make doctor
BENCHMARK_CONFIG=configs/<model>-smoke.env caffeinate -i make smoke
```

Capture launch stdout/stderr in a new `logs/` file. The launch log prints the run
ID; detailed output goes to `results/raw/<run-id>/stdout.log` and `stderr.log`.
`make smoke` always forces three tasks. For an explicitly requested larger run,
use `scripts/run-aider.sh` with a matching task count/manifest instead.

Monitor task `.aider.results.json` records, logs and `stats.csv`. Aider uses
non-streaming responses; output can be quiet for several minutes while Ollama
is generating. Inspect runtime/container health before assuming it is stuck.
Send concise progress updates during long runs, about once a minute.

In restricted agent environments, localhost, Docker sockets, network downloads
and `sysctl` may be blocked even when services are healthy. Use the environment's
normal permission mechanism to verify native access before diagnosing failure.
Do not change service bind addresses just to bypass a sandbox.

If interrupted, inspect the runner process, the specific `llm-bench-*` container,
metadata and raw artifacts. Reattach/monitor an existing run where possible.
Stop only this experiment's process/container if needed, preferring SIGINT or
SIGTERM so the runner can save partial results. Never mark stale `running`
metadata as `completed` without evidence. Keep partial artifacts; there is no
supported in-place resume command in this repository.

## Finish and hand off

The runner summarizes automatically. `make summarize` regenerates summaries
from saved metadata/artifacts without running the model. Verify the final status,
exit code, selected/completed/unknown counts, task timing records and before/after
model digest. Check runtime context with Ollama's `/api/ps` while the model is
resident and save the observation if useful; this does not verify every option.

Write/update the experiment note under `docs/`, update README result references
when needed, and report the outcome and artifact links. Update `docs/HANDOFF.md`
before ending a run or handing work to another agent, including:

- Active run ID, process/container identity and log paths, if still running.
- Completed results and verification, or the precise blocker/error.
- Current config/model, pending user request and the concrete next action.
- Changes made, unresolved limitations, and commands needed to resume monitoring.

Do not commit or push solely to preserve context unless requested; files on disk
are the handoff. Review raw artifacts before any requested publication.

For runner changes, run `make check` (shell syntax plus synthetic tests). Never
execute generated solutions on the host as a verification shortcut. For docs-only
changes, check links/facts and `git diff --check`; CSV uses standard CRLF, so
`git -c core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol diff --check`
avoids reporting CSV line endings as trailing whitespace.

# local-llm-mac-benchmark

Reproducible experiments for local coding assistants on Apple Silicon, starting
with a **MacBook Air with 24 GB unified memory**, **Ollama**, and **Aider Polyglot**.
This repository stores methodology, configuration, scripts, raw outputs, and
summaries. The [first three-task smoke run](docs/experiment-20261003-smoke.md)
completed on 2026-10-03 with `qwen2.5-coder:7b`: 0/3 tasks passed. This validates
the execution pipeline, not a representative model-quality estimate.

The goal is to make coding task success rate and system resource usage auditable
on an everyday laptop. Benchmark correctness, model quality, and hardware
performance are different questions; a pass rate does not measure intelligence.

## What runs where

```text
Mac host: orchestration + native stats → Ollama (local inference)
                  │                         ↑
                  └─ Docker: Aider harness ──┘
                              + generated code + exercise tests
                  ↓
       raw artifacts + metadata → standard-library CSV/JSON summaries
```

[Aider Polyglot](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/benchmark/README.md)
uses coding exercises across six languages. This runner selects **3 tasks by
default**, one at a time; it does not implicitly run the full suite.

Collected metrics: passed/failed/unknown tasks, complete-run and per-language pass
rates, task wall time, run wall time, sampled host memory/swap/CPU/load, and battery
endpoints. Tokens/sec, exact temperature, and watts are currently unsupported.
See [metric definitions](docs/metrics.md).

## Requirements

- Apple Silicon macOS, native arm64 Python **3.9+**, and Git.
- [Docker Desktop for Mac](https://docs.docker.com/desktop/setup/install/mac-install/),
  with its daemon running and sufficient VM memory/disk space for six language toolchains.
- [Ollama](https://ollama.com/download/mac) running **on the Mac**, with a locally
  installed model that fits alongside macOS and Docker. No model is downloaded by scripts.
- Internet access for source setup, the explicit image build, and potentially
  language-package downloads during exercise tests.

Host scripts use only Python's standard library and macOS tools. Aider and its
Python/language dependencies are installed inside the Docker image.

## Quick start

From a clone of this repository:

```bash
cp configs/benchmark.example.env configs/benchmark.env
# Edit MODEL_NAME to an exact installed Ollama name:tag (from `ollama list`).
# Select/pull a suitable model yourself if none is installed.
make setup        # clones only the two source repositories, at recorded SHAs
make build-image  # explicit, potentially large toolchain/dependency build
make doctor
make system-info
```

Start Docker Desktop and Ollama before `make doctor`. Local configuration is
parsed as `KEY=VALUE`, never sourced as shell code. Environment variables take
precedence. `BENCHMARK_CONFIG=/path/to/experiment.env` selects another config.
Model templates are standalone examples, not automatically merged.

The host uses `OLLAMA_BASE_URL=http://127.0.0.1:11434`; the container uses
`OLLAMA_DOCKER_BASE_URL=http://host.docker.internal:11434`. The runner checks that
the container can see the same model digest before starting tasks. If it cannot,
check Docker-to-host networking and the Ollama bind address. Follow the
[Ollama server configuration guide](https://docs.ollama.com/faq#how-do-i-configure-ollama-server).
Do not expose an unauthenticated Ollama endpoint to an untrusted network.
Use Ollama's local-only mode (`OLLAMA_NO_CLOUD=1` on the server) when supported.

## Start a three-task smoke test

After dependencies and the model are ready:

```bash
make smoke
make summarize
```

`make smoke` always forces `BENCHMARK_TEST_COUNT=3`. Direct invocation also defaults
to three, but honors an explicit count in your config or environment:

```bash
./scripts/run-aider.sh
BENCHMARK_TEST_COUNT=10 RUN_LABEL=ten-task ./scripts/run-aider.sh
```

Zero and negative counts are rejected. A smoke test validates the pipeline; three
tasks are not a representative model-quality estimate. Logs stream to files; use
`tail -f results/raw/<run-id>/stdout.log` in another terminal to watch progress.
Ctrl-C stops this run's container and saves partial metadata where possible.

## Artifacts and reproduction

```text
configs/dependencies.json              # exact source commit pins
results/raw/<run-id>/
  configuration.json, tasks.json       # effective settings and ordered task paths
  model-settings.yml, command.json     # temperature/context settings and command
  container-entry.py                   # exact adapter used
  python-packages.txt                  # image Python package inventory
  stdout.log, stderr.log, stats.csv
  aider/<language>/exercises/practice/<task>/
    .aider.results.json, .benchmark.timing.json, histories, generated files
metadata/runs/<run-id>.json             # extensible schema v1, state and observations
results/summary/results.csv            # one row per recorded run
results/summary/<run-id>.json           # task/per-language details, nulls preserved
```

Empty CSV cells mean unavailable, not zero. Incomplete tasks are unknown, not
failed. An overall pass rate is left empty until every selected task has a valid
outcome. See [schema](docs/metadata.md) and [methodology](docs/methodology.md).

To repeat a subset, restore the recorded non-secret settings and set:

```bash
TASK_MANIFEST=results/raw/<run-id>/tasks.json BENCHMARK_TEST_COUNT=3 \
  RUN_LABEL=repeat ./scripts/run-aider.sh
```

Use the original task count, model digest/quantization, source pins, and Docker
image ID. Commit your experiment configuration and repository code before formal
runs; an unborn Git repository has a null commit and a dirty checkout is flagged.
Pinning source does **not** freeze upstream package repositories. Preserve the
built image separately (`docker image save …`) for closer reproduction and record
its digest; large image archives are ignored. Identical outputs are not guaranteed
even at temperature zero. See [limitations](docs/limitations.md).

## Safety and publication

**The benchmark executes code generated by an LLM. Run it only in Docker/sandbox,
never directly on the host.** The runner mounts only the current run directory
writable and the exercises read-only; it does not mount your home, Docker socket,
or repository checkout, and does not forward API secrets. It drops Linux
capabilities, prevents privilege escalation, and limits memory/CPU/processes.
Docker is a risk reduction, not a security proof: the container has network
access, can contact Ollama, and can modify its own raw artifacts. Use a disposable
machine/VM for stronger isolation. Do not execute generated scripts on the host.

Review artifacts before committing: logs/generated text can contain arbitrary
content, and the requested hostname can be identifying. System collection omits
usernames, home paths, serial numbers and hardware UUIDs. Config/model weight/cache
files are ignored as appropriate; raw results, metadata and summaries remain
committable. Third-party exercise/code/model licenses still apply.

## Development and scope

`make check` performs shell syntax checks and isolated unit/integration tests;
tests use synthetic data only in temporary directories and never run a model.
Use `shellcheck scripts/*.sh` as an additional check if installed.

Shell entry points delegate to `scripts/benchmark.py` to avoid duplicate parsing
and metadata logic. `scripts/container-entry.py` adapts the pinned upstream
harness without modifying its source. Future `benchmarks/` and `runtimes/`
adapters can share the versioned metadata envelope; MLX, llama.cpp, LM Studio,
HumanEval, MBPP and SWE-bench are not implemented in this version.

# Benchmark handoff

Last updated: 2026-10-03 (Asia/Bangkok), after both smoke runs completed and
the user requested instructions so Claude Code can continue after context loss.

## Current task and next action

The current request is to create agent handoff instructions. It does not request
a third benchmark. Both previous runs finished; no unfinished run or selected
third model is recorded at this checkpoint. Do not restart either completed run.
If the user asks for the next model, choose a suitable local model, explain the
choice briefly, and run the same three-task subset following `AGENTS.md`.

Before resuming, verify `git status --short`, latest run metadata, `docker ps`
and runner processes: another agent/user may have advanced the work since this
snapshot. Do not rely on tool session IDs from the previous chat.

## Completed experiments

| Model | Run ID | Status | Passed | Wall time |
| --- | --- | --- | ---: | ---: |
| `qwen2.5-coder:7b` | `20261003T035503Z-smoke-ae34538d` | completed | 0/3 | 404.31 s |
| `qwen3.5:9b` | `20261003T040917Z-qwen35-9b-smoke-0deb827c` | completed | 0/3 | 850.65 s |

Both have exit code 0, all three scored tasks, no unknown outcomes, no reported
test timeouts/task exceptions, and unchanged model digests before/after.
Every task had `[false, false]` test outcomes. No generated solutions were
manually repaired. A task needs its entire test suite to pass.

The task manifest is Python `forth`, Go `alphametics`, Java `rational-numbers`,
in that order. It is stored in the first raw run and explicitly replayed by the
second. Image ID, adapter hash and task manifests matched between runs.

- [First experiment](experiment-20261003-smoke.md): Python failed 54 tests;
  Go failed compilation; Java passed 39/41 unit tests.
- [Second experiment](experiment-20261003-qwen35-9b.md): Python passed 9/54
  tests; Go compiled on retry but failed correctness tests; Java passed 39/41.
- [Combined CSV](../results/summary/results.csv) contains both runs.
- Full metadata: `metadata/runs/<run-id>.json`.
- Raw outputs: `results/raw/<run-id>/`, including exact configurations,
  `command.json`, model settings, package inventory, histories, task records,
  timing files, stdout/stderr, `stats.csv` and `ollama-ps-during.json`.

## Existing setup (recheck before reuse)

- Host observed: Apple M5 MacBook Air, 24 GiB unified memory, macOS 26.6.2,
  native arm64 Python 3.9.6. See `hardware/system-info-20261003.json`.
- Ollama 0.35.1; downloaded models: `qwen2.5-coder:7b`, `qwen3.5:9b`.
- Docker 29.8.1; VM observed with 10 CPUs and 8,319,504,384 bytes memory.
- Image: `local-llm-aider-benchmark:pinned`, native arm64. Already built.
  Inspect exact image IDs in run metadata; do not rebuild unnecessarily.
- Sources are already fetched under ignored `.deps/`, at the pins in
  `configs/dependencies.json`. `make setup` is not needed if checks still pass.
- Both models use Q4_K_M. Context 8192 was observed through `/api/ps`.
- Controls: temperature requested 0, whole-file editing, two attempts,
  one worker, seed 0, 6 GiB container RAM and 4 CPUs.
- Tracked config for the second run: `configs/qwen35-9b-smoke.env`.
  Ignored `configs/benchmark.env` still selected `qwen2.5-coder:7b` at the
  checkpoint. Always specify `BENCHMARK_CONFIG` when running another model.
- `make check` passed all 15 tests before the first run; no runner changes were
  made for the second. `make doctor` passed for each real run. Final artifacts
  and summaries were verified for both runs.
- Git HEAD before adding these handoff files: `13e4ed1` (`qwen3.5:9b`), with
  a clean working tree. Previous result commit: `bba6fdd` (`wen2.5-coder:7b`).
  Recheck current Git state rather than resetting to these commits.

## Important interpretation and troubleshooting notes

1. These are three-task smoke runs, not full Polyglot scores. The second took
   about 2.10 times the wall time; this is not a general model speed ranking.
2. Aider automatically chose history summarization thresholds of 2048 tokens
   for Qwen2.5 and 8192 for Qwen3.5. Both runtime contexts were 8192. Other model
   defaults differ; thinking mode and effective temperature were not traced.
3. Both runs were on AC. First run periodic peak swap: 117.44 MiB. Second run
   already started with 1,735.62 MiB swap, peaked at 2,658.81 MiB in periodic
   samples, and ended with 2,672.69 MiB in the separate after-run observation.
   Whole-host/background/cooling conditions were not controlled.
4. Initial sandbox probes falsely appeared unable to access Docker/Ollama.
   Native probes confirmed both services were healthy. Use environment
   permissions appropriately; do not assume another installation is needed.
5. Qwen3.5 Go generation had long silent intervals. Native Ollama timing logs
   showed ongoing generation. There was no need to kill/restart it.
6. First run printed Aider background chat-summarizer shutdown warnings after
   task records were complete; host CSV/JSON summary still succeeded. Preserve
   and report warnings rather than discarding otherwise complete artifacts.
7. The model name alone is not sufficient reproduction evidence; preserve
   digest, saved config, task manifest, source pins, image ID and adapter hash.

## Keep this handoff current

After the next requested experiment, replace the current-task section with the
actual remaining work and add the result/config/report links. If context is
nearly exhausted mid-run, record its run ID, process/container identity, launch
log and last verified progress so the next agent monitors it rather than starts
a duplicate. Never claim a running or partial experiment has finished.

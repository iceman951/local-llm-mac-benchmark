# First local smoke benchmark — 2026-10-03

Date: 2026-10-03 (Asia/Bangkok). Purpose: validate the real local inference,
container harness and artifact pipeline with the repository's default three
tasks. This subset is not a representative model-quality estimate.

## Planned controls

- Model: `qwen2.5-coder:7b`, selected after the user authorized model selection
  and download. Ollama lists this coding model as 7.62B / Q4_K_M / approximately
  4.7 GB: <https://ollama.com/library/qwen2.5-coder:7b>.
- Host: Apple M5, 24 GiB unified memory; full observation in
  `hardware/system-info-20261003.json`.
- AC power; initial battery 69%, charging. Low Power Mode disabled for both
  AC and battery profiles. Battery drop will not be interpreted as energy use.
- Docker VM: 10 CPUs, 8,319,504,384 bytes RAM; no containers running at initial
  inspection. Benchmark container: 4 CPUs, 6 GiB RAM, no additional swap.
- Context 8192, temperature 0, whole-file editing, at most two attempts,
  one worker, selection seed 0.
- Ordered tasks: Python `forth`, Go `alphametics`, Java `rational-numbers`.
- No model resident at initial `/api/ps` inspection. No warm-up requested.
  Model download and image build precede this smoke run; no controlled cooling
  interval or cold operating-system cache is claimed.
- Background applications were not closed. Ambient temperature and physical
  cooling conditions were not measured. This is pipeline validation.

## Preparation evidence

- `make check`: all 15 tests passed; shell syntax checks passed.
- Docker and Ollama API were confirmed outside the execution sandbox. Initial
  sandbox connectivity failures did not indicate service failure.
- Both source dependencies fetched at the commits in `configs/dependencies.json`.
- Setup, model download and image-build output are preserved under `logs/`.
- `make doctor`: all checks passed before the run; see `logs/doctor-20261003.log`.
- Runtime model digest, image ID, source pins, resource samples and task results
  are recorded by the runner under `metadata/runs/` and `results/raw/`.

## Outcome

Run ID: `20261003T035503Z-smoke-ae34538d`. Started around 10:55 and finalized
at 11:01:49 Asia/Bangkok. Status: `completed`, runner exit code 0, three scored
tasks, no unknown outcomes. Model digest was unchanged after execution.

| Task | Attempt outcomes | Task wall time | Final observation |
| --- | --- | ---: | --- |
| Python `forth` | fail, fail | 104.64 s | 54 tests failed; generated code treats the list input as a string |
| Go `alphametics` | fail, fail | 122.98 s | Generated code failed compilation with string/slice/map type mismatches |
| Java `rational-numbers` | fail, fail | 139.79 s | 39 of 41 unit tests passed; two real-number exponentiation cases failed |

Overall task pass rate: **0/3 (0%)** under this configuration. A task passes only
when its complete test suite passes; Java's partial unit-test success is not a
passed task. No benchmark test timeouts or task exception records were reported.
Reviewed failure output points to generated-code errors rather than missing
toolchains. Generated solutions were not manually repaired.

- Run wall time: **404.31 s (6 min 44 s)**, excluding initial setup/image build.
- Mean measured task wall time: **122.47 s**.
- Peak sampled host memory: **23,868.55 MiB (23.31 GiB)**. This is the repo's
  whole-host page-based metric, including other processes and reclaimable pages,
  not model-only memory or a measure of memory pressure.
- Peak sampled host swap used: **117.44 MiB**; it appeared late in the run.
- Battery: 73% to 75% on AC; battery consumption is unavailable.
- `/api/ps` confirmed context length **8192**, Q4_K_M and resident size equal to
  reported GPU allocation (4,979,792,280 bytes). See `ollama-ps-during.json`
  within the raw run directory. Temperature was requested as 0; effective
  temperature was not independently observed from server request tracing.
- The upstream Aider background chat summarizer printed shutdown warnings
  (`cannot schedule new futures after shutdown`) after all task records and
  upstream statistics were emitted. The host CSV/JSON result summary completed
  successfully. These warnings are preserved in `stdout.log`.
- This smoke run used the current repository commit with uncommitted experiment
  artifacts, recorded as a dirty checkout; it is not a formal clean-checkout run.

Artifacts:

- [Summary CSV](../results/summary/results.csv)
- [Detailed summary](../results/summary/20261003T035503Z-smoke-ae34538d.json)
- [Run metadata](../metadata/runs/20261003T035503Z-smoke-ae34538d.json)
- [Raw stdout](../results/raw/20261003T035503Z-smoke-ae34538d/stdout.log)
- [Host samples](../results/raw/20261003T035503Z-smoke-ae34538d/stats.csv)

No full-suite run or additional model comparison was performed.

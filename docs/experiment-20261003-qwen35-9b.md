# Qwen3.5 9B smoke benchmark — 2026-10-03

Purpose: run the next local model on the exact three tasks from
`20261003T035503Z-smoke-ae34538d`. This is a small pipeline/model comparison,
not a full-suite estimate or controlled hardware comparison.

## Controls and initial conditions

- Model: `qwen3.5:9b`; official Ollama listing: approximately 6.6 GB,
  9.65B parameters, Q4_K_M. Source: <https://ollama.com/library/qwen3.5:9b>.
- Configuration: `configs/qwen35-9b-smoke.env`; replay the first run's task
  manifest: Python `forth`, Go `alphametics`, Java `rational-numbers`.
- Same context 8192, requested temperature 0, whole-file edits, two attempts,
  one worker, Docker image, 6 GiB container limit and 4 CPUs as the first run.
- No explicit thinking override: model/runtime defaults apply. This model
  supports thinking; generation time is not a fixed reasoning-budget comparison.
  Other model sampling defaults can differ and are recorded in run metadata.
- Aider automatically selected `max_chat_history_tokens=8192` for this model,
  versus 2048 for the first model. Runtime context is 8192 in both runs, but
  the harness's automatic history summarization threshold is not identical.
- No resident model or running Docker container at initial inspection.
  No inference warm-up; OS caches were not cleared.
- AC power, initial battery 79%, charging. Background applications were left
  open. Host swap already used 1,735.62 MiB before downloading this model;
  peak swap is total host usage and must not be attributed solely to this run.
- No controlled cooling interval or ambient temperature measurement.
- Existing sources and built image are reused. Model download time is excluded
  from benchmark wall time.

## Outcome

Run ID: `20261003T040917Z-qwen35-9b-smoke-0deb827c`. Started around 11:09 and
finalized at 11:23:30 Asia/Bangkok. Status `completed`, exit code 0, three scored
tasks and no unknown outcomes. Model digest was unchanged after the run.

| Task | Attempt outcomes | Task wall time | Final observation |
| --- | --- | ---: | --- |
| Python `forth` | fail, fail | 195.50 s | 9/54 unit tests passed; 45 failed |
| Go `alphametics` | fail, fail | 393.58 s | First response failed compilation; second compiled but failed correctness tests |
| Java `rational-numbers` | fail, fail | 256.89 s | 39/41 unit tests passed; two real-number exponentiation cases failed |

Overall task pass rate: **0/3 (0%)**. Partial unit-test success does not count as
a passed task. No task exceptions, test timeouts or exhausted-context events
were reported by the harness. Reviewed output shows generated-code failures;
solutions were not manually repaired.

- Run wall time: **850.65 s (14 min 11 s)**, excluding the model download.
- Mean measured task wall time: **281.99 s**.
- Peak sampled host memory: **23,865.03 MiB (23.31 GiB)**. This whole-host
  page-based metric includes other processes and reclaimable pages; it is not
  model-only memory or a measure of memory pressure.
- Peak swap in periodic samples: **2,658.81 MiB**. The separate after-run
  observation was **2,672.69 MiB**, versus **1,735.62 MiB** before the run.
  These are total host values with uncontrolled background activity.
- AC power throughout, battery 80% to 80%; battery consumption unavailable.
- Ollama's resident-model API confirmed context **8192** and Q4_K_M, with
  resident size and GPU allocation both **5,774,759,688 bytes**. The file
  download size is different from resident inference allocation. Evidence:
  `ollama-ps-during.json` in the raw run directory.
- Requested temperature remained 0. Effective temperature and thinking mode
  were not independently verified through request tracing.
- All preflight checks passed. Image ID, adapter hash and task manifest were
  checked against the first run and matched exactly. Both runs used the same
  source pins. No runner implementation changes were made for this run.

## Comparison with the first smoke run

| Model | Passed tasks | Run wall time | Python | Go | Java |
| --- | ---: | ---: | ---: | ---: | ---: |
| `qwen2.5-coder:7b` | 0/3 | 404.31 s | 104.64 s | 122.98 s | 139.79 s |
| `qwen3.5:9b` | 0/3 | 850.65 s | 195.50 s | 393.58 s | 256.89 s |

The second run took approximately 2.10 times the wall time on this subset.
This does not establish a general speed or quality ranking: there is one run
per model, only three tasks, differing model defaults and Aider history
thresholds, and different starting swap/background conditions.

Artifacts:

- [Combined summary CSV](../results/summary/results.csv)
- [Detailed summary](../results/summary/20261003T040917Z-qwen35-9b-smoke-0deb827c.json)
- [Run metadata](../metadata/runs/20261003T040917Z-qwen35-9b-smoke-0deb827c.json)
- [Raw stdout](../results/raw/20261003T040917Z-qwen35-9b-smoke-0deb827c/stdout.log)
- [Host samples](../results/raw/20261003T040917Z-qwen35-9b-smoke-0deb827c/stats.csv)
- [Reproduction configuration](../configs/qwen35-9b-smoke.env)

No full-suite run was performed.

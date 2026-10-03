# Qwen2.5-Coder 14B smoke benchmark — 2026-10-03

Purpose: test a larger model in the same coding family as the initial 7B model,
using the same three-task subset and benchmark controls. This is not a full
Polyglot score or a controlled hardware comparison.

## Controls and initial conditions

- Model: `qwen2.5-coder:14b`; official Ollama listing: 14.8B parameters,
  Q4_K_M, approximately 9.0 GB download.
  Source: <https://ollama.com/library/qwen2.5-coder:14b>.
- Configuration: `configs/qwen25-coder-14b-smoke.env`.
- Task manifest from `20261003T035503Z-smoke-ae34538d`: Python `forth`, Go
  `alphametics`, Java `rational-numbers`, in that order.
- Requested context 8192, temperature 0, whole-file editing, at most two
  attempts, one worker, seed 0. Docker container: 6 GiB RAM, 4 CPUs.
- Existing image and pinned sources reused; no runner implementation changes.
- Before download: no resident Ollama model, running Docker container or
  benchmark runner process found. No inference warm-up; OS caches not cleared.
- AC power, battery 80%, not charging. Existing host swap used 2,544.12 MiB.
  Background applications were not closed. Cooling interval and ambient
  conditions were not controlled. File download time is excluded from run time.
- Model residency, exact digest, actual run baseline and Docker resources are
  recorded in runtime metadata. Effective sampling parameters are not inferred
  from configuration alone.

## Outcome

Run ID: `20261003T043750Z-qwen25-coder-14b-smoke-7a3e6cf3`. Started around 11:37
and finalized at 12:03:41 Asia/Bangkok. Status `completed`, exit code 0, three
scored tasks and no unknown outcomes. Model digest was unchanged after the run.
All preflight checks passed. Image ID, adapter hash and task manifest match the
first run. No runner implementation changes were made for this run.

| Task | Attempt outcomes | Task wall time | Final observation |
| --- | --- | ---: | --- |
| Python `forth` | fail, fail | 901.21 s | Both attempts ended with a `SyntaxError` (tuple assignment inside a lambda); pytest collection failed, so no unit tests ran |
| Go `alphametics` | fail, fail | 305.60 s | First response failed compilation (unused imports); second compiled; 2/10 cases passed (the two expected-error cases), all 8 solvable puzzles returned no solution |
| Java `rational-numbers` | fail, fail | 268.14 s | 39/41 unit tests passed; the two real-number exponentiation cases failed |

Overall task pass rate: **0/3 (0%)**. Partial unit-test success does not count as
a passed task. The harness reported no task exceptions, test timeouts,
malformed responses or exhausted-context events. Reviewed output shows
generated-code failures, not missing toolchains, network failures or timeouts;
solutions were not manually repaired.

- Run wall time: **1,548.59 s (25 min 49 s)**, excluding the model download.
- Mean measured task wall time: **491.65 s**.
- Python `forth` dominated the run time. Aider repeatedly asked the model to fix
  the flake8 `E999` syntax error (8 lint-fix rounds across both attempts;
  43,461 prompt tokens for this task versus 3,936 for Go and 6,366 for Java).
  The model returned an unchanged syntax error each time.
- Ollama's server log recorded two `slot context shift` events (n_discard 4093)
  during `/api/chat` requests completing at 11:50:06 and 11:52:57, both within
  the Python task. A request's prompt plus generated tokens therefore reached
  the 8192 runtime context and the runtime discarded earlier tokens. Aider did
  not report this as an exhausted context window. Each of these requests took
  over two minutes.
- Peak sampled host memory: **23,866.13 MiB (23.31 GiB)**, a whole-host
  page-based metric that is not model-only memory.
- Peak swap in periodic samples: **9,526.88 MiB**. The after-run observation was
  **9,435.19 MiB**, versus **2,496.06 MiB** before the run. These are total host
  values with uncontrolled background applications. The roughly 10 GB resident
  model plus the 8 GiB Docker VM exceed what the 24 GiB host can hold alongside
  other applications without heavy swapping. Swap may have affected wall time;
  this run's timing is not a clean speed measurement.
- AC power throughout, battery 80% to 80%; battery consumption unavailable.
- Ollama `/api/ps` confirmed Q4_K_M, context 8192, and matching resident/GPU
  allocation of 10,269,113,711 bytes (`ollama-ps-during.json`).
- Aider's automatic history summarization threshold was 2048, the same as the
  7B run. Requested temperature remained 0; effective sampling parameters were
  not independently verified through request tracing.
- Startup output reported a five-second read timeout fetching from
  `raw.githubusercontent.com`; the harness proceeded to inference.
- After the task records were complete, Aider printed background
  chat-summarizer shutdown warnings (`cannot schedule new futures after
  shutdown`), as in the first run. Host CSV/JSON summarization succeeded.

## Comparison with earlier smoke runs

| Model | Passed tasks | Run wall time | Python | Go | Java |
| --- | ---: | ---: | ---: | ---: | ---: |
| `qwen2.5-coder:7b` | 0/3 | 404.31 s | 104.64 s | 122.98 s | 139.79 s |
| `qwen3.5:9b` | 0/3 | 850.65 s | 195.50 s | 393.58 s | 256.89 s |
| `qwen2.5-coder:14b` | 0/3 | 1,548.59 s | 901.21 s | 305.60 s | 268.14 s |

The 14B model produced the same outcome as both earlier models on this subset:
0/3, with Java at 39/41 unit tests in every run. On Python it did worse in
partial terms than Qwen3.5 9B (no tests ran, versus 9/54). This does not
establish a general quality or speed ranking: there is one run per model, only
three tasks, different model defaults, and much higher host swap in this run.

Artifacts:

- [Combined summary CSV](../results/summary/results.csv)
- [Detailed summary](../results/summary/20261003T043750Z-qwen25-coder-14b-smoke-7a3e6cf3.json)
- [Run metadata](../metadata/runs/20261003T043750Z-qwen25-coder-14b-smoke-7a3e6cf3.json)
- [Raw stdout](../results/raw/20261003T043750Z-qwen25-coder-14b-smoke-7a3e6cf3/stdout.log)
- [Host samples](../results/raw/20261003T043750Z-qwen25-coder-14b-smoke-7a3e6cf3/stats.csv)
- [Reproduction configuration](../configs/qwen25-coder-14b-smoke.env)

No full-suite run was performed.

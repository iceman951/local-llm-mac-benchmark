# Ornith 9B smoke benchmark — 2026-10-03

Purpose: test a recent agentic-coding fine-tune that fits the 24 GiB memory
budget, on the same three tasks and controls as earlier runs. It is directly
comparable in base architecture and size with `qwen3.5:9b`. This is not a full
Polyglot score or a controlled hardware comparison.

## Controls and initial conditions

- Model: `ornith:9b`; official Ollama listing: 8.95B parameters, Q4_K_M,
  5.6 GB download, MIT license, Qwen3.5 architecture (`qwen35`), tools and
  thinking capabilities, ID `a75697c14589`.
  Source: <https://ollama.com/library/ornith:9b>.
- Selection rationale: `qwen3.8:27b` (18 GB) and `ornith:35b` (21 GB) exceed
  the budget; the 14B run already swapped heavily.
- Configuration: `configs/ornith-9b-smoke.env` — a copy of
  `configs/qwen35-9b-smoke.env` with only `MODEL_NAME` and `RUN_LABEL` changed.
- Task manifest from `20261003T035503Z-smoke-ae34538d` (byte-identical copy):
  Python `forth`, Go `alphametics`, Java `rational-numbers`, in that order.
- Requested context 8192, temperature 0, whole-file editing, at most two
  attempts, one worker, seed 0. Docker container: 6 GiB RAM, 4 CPUs.
- No explicit thinking override: model/runtime defaults apply. The model's
  Ollama defaults are temperature 0.6, top_k 20, top_p 0.95; the requested
  temperature 0 was sent by the harness, but effective sampling parameters
  were not verified through request tracing.
- Aider automatically selected `max_chat_history_tokens=8192`, as for
  `qwen3.5:9b`.
- Download log: `logs/model-pull-ornith-9b-20261003.log`. Doctor passed:
  `logs/doctor-ornith-9b-20261003.log`. Download time is excluded.
- Before the run: no resident model, no running Docker container, AC power,
  battery 80% not charging. Host swap already used 6,778 MiB, left over from
  the earlier 14B run. Background applications were not closed. No warm-up;
  OS caches not cleared; cooling and ambient conditions not controlled.

## Outcome

Run ID: `20261003T055010Z-ornith-9b-smoke-a49f7a44`. Started 12:50 and finalized
at 13:15:55 Asia/Bangkok. Status `completed`, exit code 0, three scored tasks and
no unknown outcomes. Model digest unchanged after the run. Image ID, adapter
hash and task manifest match the earlier runs. No runner changes were made.

| Task | Attempt outcomes | Task wall time | Final observation |
| --- | --- | ---: | --- |
| Python `forth` | fail, fail | 353.96 s | No code was applied; the stub was unchanged and all 54 tests failed |
| Go `alphametics` | fail, fail | 860.59 s | No code was applied; the stub panicked with "Please implement the Solve function" |
| Java `rational-numbers` | fail, fail | 323.97 s | Code applied; 39/41 unit tests passed in both attempts; the two real-number exponentiation cases failed |

Overall task pass rate: **0/3 (0%)**. The harness reported no task exceptions,
test timeouts, malformed responses or exhausted-context events. Solutions were
not manually repaired.

### Failure mode: thinking consumed the context window

Aider's output splits each response into **THINKING** and **ANSWER** sections.
For all four Python and Go responses, the ANSWER section was empty, so the
whole-file editor had nothing to apply:

| Response | Prompt tokens | Received tokens |
| --- | ---: | ---: |
| Python attempt 1 | 1.5k | 6.7k |
| Python attempt 2 | 8.2k | 9 |
| Go attempt 1 | 1.2k | 7.0k |
| Go attempt 2 | 1.6k | 6.6k |

In Python attempt 1, the reasoning block contained several full draft
implementations ("Wait, I'm still repeating myself...") and ended mid-code at
roughly the 8192-token runtime context. The second attempt's prompt nearly
filled the context, leaving room for only 9 tokens. Go followed the same
pattern. Java needed less reasoning (1.1k and 3.4k received tokens) and
produced applied code.

This is a recorded outcome under the fixed controls (context 8192, default
thinking). It means this run measures the interaction of a thinking model with
an 8192 context more than the model's coding ability. A larger context or
disabled thinking would be a new experimental condition, not a rerun of this
one.

### Resources and timing

- Run wall time: **1,543.09 s (25 min 43 s)**; mean task wall time
  **512.84 s**. Most time was spent generating reasoning that was never applied.
- Generation rate seen in the Ollama server log at the start of the run: about
  23 tokens/s (single observation, not a summary metric).
- Peak sampled host memory: **23,862.19 MiB**, a whole-host page-based metric
  that is not model-only memory.
- Swap: **6,778 MiB** before (also the periodic peak) and **6,682 MiB** after.
  Unlike the 14B run, swap did not grow during this run.
- AC power throughout, battery 80% to 80%; battery consumption unavailable.
- Ollama `/api/ps`, saved about 30 s after the run finished while the model was
  still resident (`ollama-ps-after.json`): Q4_K_M, context 8192, resident/GPU
  allocation 6,157,510,900 bytes. An `ollama ps` CLI check at 12:50:32, during
  the run, also showed 6.2 GB, 100% GPU, context 8192. The runner does not
  capture this automatically; earlier runs' `ollama-ps-during.json` files were
  saved separately during those runs.

## Comparison with earlier smoke runs

| Model | Passed tasks | Run wall time | Python | Go | Java |
| --- | ---: | ---: | ---: | ---: | ---: |
| `qwen2.5-coder:7b` | 0/3 | 404.31 s | 104.64 s | 122.98 s | 139.79 s |
| `qwen3.5:9b` | 0/3 | 850.65 s | 195.50 s | 393.58 s | 256.89 s |
| `qwen2.5-coder:14b` | 0/3 | 1,548.59 s | 901.21 s | 305.60 s | 268.14 s |
| `ornith:9b` | 0/3 | 1,543.09 s | 353.96 s | 860.59 s | 323.97 s |

All four models scored 0/3; Java reached 39/41 in every run. Ornith produced
no applied code for Python or Go, unlike its base family's `qwen3.5:9b`
(Python 9/54, Go compiled on retry). One run per model on three tasks does not
support a ranking.

Artifacts:

- [Combined summary CSV](../results/summary/results.csv)
- [Detailed summary](../results/summary/20261003T055010Z-ornith-9b-smoke-a49f7a44.json)
- [Run metadata](../metadata/runs/20261003T055010Z-ornith-9b-smoke-a49f7a44.json)
- [Raw stdout](../results/raw/20261003T055010Z-ornith-9b-smoke-a49f7a44/stdout.log)
- [Host samples](../results/raw/20261003T055010Z-ornith-9b-smoke-a49f7a44/stats.csv)
- [Reproduction configuration](../configs/ornith-9b-smoke.env)

No full-suite run was performed.

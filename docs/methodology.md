# Methodology

## Questions and controls

Report three separate findings: (1) **benchmark correctness** (did the harness and
tests execute as intended?), (2) **model quality** (coding task success under this
prompt/edit/retry configuration), and (3) **hardware performance** (elapsed time
and resource use under specified system conditions). None measures intelligence.

Keep a single exact Ollama model identifier, digest, quantization, context size,
temperature, edit format, and attempt limit throughout each run. The runner uses
`ollama_chat/<identifier>`, explicitly requests temperature 0 and the configured
context size through upstream model settings, and uses the same weak model.
Defaults: 3 tasks, 1 worker, 2 attempts, `whole` edits, context 8192, seed 0.
These are experiment controls, not a recommendation that all models fit 24 GB.
Runtime support for requested parameters and actual context truncation must be
verified when introducing a new model/runtime; recorded settings are requests,
not proof of exact runtime behavior.

The main coding task outcome is the last boolean unit-test outcome after at most
the configured attempts, following the pinned upstream harness. A test failure
can come from a model error or a toolchain/test problem. Review raw histories and
stderr before interpreting it as model quality. Exception-only, malformed, empty,
or missing result files are unknown. Unknown tasks prevent an overall pass rate.

## Before each experiment

1. Commit repository/config changes, record intended model/tag and verify disk/RAM
   headroom. Use a clean pinned checkout of both upstream repositories.
2. Close unnecessary applications. Stop other inference requests and unrelated
   Docker workloads. Do not change model tags during the run.
3. Record power source, Low Power Mode, room conditions and cooling/rest interval
   in a reviewed non-secret experiment note. Keep them constant across comparisons.
4. Choose either battery or AC operation. For battery-drop comparisons, remain on
   battery throughout; plugged-in and mixed-source runs do not measure consumption.
5. Fix Docker VM resources and per-container limits. Defaults constrain the
   container to 6 GiB, 4 CPUs, no additional swap, and 512 processes. Docker VM
   allocation is separate and is recorded when available.
6. Decide cold/warm conditions. The runner does not preload or evict models and
   does not clear system caches. Record prior model residency; use consistent
   preparation and separate warm-up runs if needed. Model load time can affect
   the first task. An unloaded-model condition is not a cold OS-cache guarantee.
7. Run `make doctor`, then a three-task smoke test. Inspect raw results to validate
   the execution path before explicitly increasing the count.

## Selection and execution

Task candidates are sorted relative exercise paths from the pinned Polyglot
checkout. A local seeded shuffle selects the first N. The chosen ordered paths
are written to `tasks.json`; this file, not the seed alone, is the authoritative
reproduction input. A container adapter replaces the harness task shuffle with
this manifest and times each task call. It checks that all selected paths exist.
This small adapter is saved and hashed per run. No exercise or test code is
changed by the host runner. The upstream harness may prepare tests as documented
in its own source. Concurrency above one changes scheduling and resource use.

The host preflight checks OS/architecture, dependencies, API, clean source pins,
image label/architecture, and writable outputs. The run checks the container's
Ollama endpoint against the recorded digest. All generated code/tests execute in
Docker. Source checkouts are not mounted writable into the container. A fresh
run directory prevents accidental continuation or reuse of existing results.

Before execution, capture UTC timestamp, hostname, macOS version/build, Darwin,
chip/model/physical memory, repository SHA/dirty state, both upstream SHAs,
Ollama server/CLI versions, Docker client/server versions, image ID/digests,
Python and Git versions, effective configuration, model details/digest/template
hash, and battery/memory/swap observations. Capture the same observations after
execution and compare the model digest again. Never collect serial numbers,
hardware UUIDs, usernames or home-directory paths.

Host polling writes CSV samples during execution. The wall timer surrounds the
benchmark container invocation and excludes setup, image build, metadata probes,
and final summarization. stdout and stderr are separate files. Each task's wall
timer includes Aider, tests, and harness overhead inside that task. Upstream's
`duration` measures its Aider calls and is retained separately.

## Analysis and reporting

Quality: report selected/completed/unknown counts, passed/failed counts, complete
pass rate, per-language counts/rates, and task durations. Include attempt count,
edit format, context size, task manifest and source pins with comparisons.

Performance: report run wall time, mean measured task wall time, sampled host
memory/swap peaks, CPU/load observations and battery endpoints. Tokens/sec,
temperature and watts are unsupported in this adapter; no proxy values are
invented. Consult [metrics](metrics.md) for exact formulas and denominators.

Repeat comparable runs after a consistent rest period; report variation rather
than selecting the best run. Predeclare subsets and repetitions for formal
comparisons. Three tasks only validate the pipeline. Do not compare a small
subset directly to the full-suite leaderboard, and do not extrapolate a laptop
run into a general hardware/model ranking.

Retain raw artifacts even when a run fails. The summary can be regenerated without
executing generated code. Mark interrupted/error/incomplete/model-changed runs
explicitly; unknown or unsupported quantities remain JSON null / CSV empty.

## Sources

- [Pinned Aider harness and its result fields](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/benchmark/benchmark.py)
- [Pinned Polyglot exercises](https://github.com/Aider-AI/polyglot-benchmark/tree/7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f)
- [Aider Ollama configuration](https://aider.chat/docs/llms/ollama.html)
- [Ollama model identifiers and digests](https://docs.ollama.com/api/tags)

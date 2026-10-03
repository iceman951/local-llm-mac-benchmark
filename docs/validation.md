# Initial validation record

Date: 2026-10-03 (Asia/Bangkok). This is an implementation validation record, not
a benchmark result. No inference, model download, Docker image build or benchmark
execution was performed during repository setup.

- `bash -n` checks all shell entry points.
- `make check` runs standard-library tests with temporary synthetic fixtures,
  including partial/malformed results, metric units, config precedence, task
  replay, the actual container adapter against a stub harness, and a simulated
  Docker runner lifecycle. Fixtures never enter `results/` or `metadata/`.
- Python source syntax and Makefile target expansion were checked separately.
- `make doctor` correctly returns a failing exit status on this machine because
  Docker, Ollama, source checkouts and the built image are unavailable.
- `make system-info` succeeds. With native read permissions it reports chip,
  hardware model and physical memory; sandboxed `sysctl` calls can return null.
  No hardware/version values are baked into configuration or documentation.
- Source pins and runner arguments/result fields were checked against the
  official upstream repositories. Local documentation paths and ignore rules
  were reviewed. No real benchmark records or secret files were added.
- ShellCheck is not installed; only shell syntax checking was performed.

Still unvalidated: fetching sources through `make setup`, building the upstream
arm64 image, package/toolchain compatibility, real Docker-to-host Ollama
connectivity, actual model parameter acceptance, and a complete three-task smoke
run. Complete these on an equipped host before publishing any quality or
performance claims. Upstream build dependencies remain mutable as documented.

## Real smoke validation follow-up — 2026-10-03

The [first real smoke experiment](experiment-20261003-smoke.md) subsequently
completed: source fetch, native arm64 image build, all preflight checks,
Docker-to-host Ollama connectivity, inference, three task outcomes, host stats,
and CSV/JSON summaries were exercised successfully. Context length 8192 was
confirmed by Ollama's resident-model API. All 15 repository tests also passed.
All three tasks failed their final tests; this is a recorded model outcome, not
a claim that the pipeline could not execute. See the experiment note for failure
details and upstream background-summarizer shutdown warnings. Effective
temperature remains requested rather than independently traced.

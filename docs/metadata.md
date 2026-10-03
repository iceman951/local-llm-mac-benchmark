# Metadata schema v1

Each `metadata/runs/<run-id>.json` contains these extensible objects:

| Field | Meaning |
| --- | --- |
| `schema_version` | Integer 1. Future incompatible schemas increment this. |
| `run_id`, `timestamp` | UTC timestamp/label/random suffix, and ISO 8601 UTC start metadata time. |
| `machine` | Allowlisted native OS/hardware/tool versions, repo SHA/dirty flag, source checkouts. |
| `runtime` | Runtime name/server version, immutable Docker image ID, available digests/architecture and VM resource allocation. |
| `model` | Resolved identifier, digest, size, quantization/details, parameters, model info and template hash; final digest when obtainable. |
| `benchmark` | Adapter name, upstream URLs/SHAs, adapter SHA-256. |
| `configuration` | Effective non-secret allowlisted values. `TASK_MANIFEST` is stored as `tasks.json` relative to the raw run. |
| `observations` | Host stats before/after execution. |
| `result` | Lifecycle state, exit code, finish timestamp, metrics and task/language results. |
| `unsupported_metrics` | Explicit list of unavailable metrics. |

States: `preparing` → `running` → `completed` or `incomplete`. Launch/probe errors
use `error`; cancellation uses `interrupted`. A changed model digest overrides the
state with `model_changed`; a failed final model check uses `unverified_model`.
Only a completed run returns success. Passing tasks do not require every task to
pass: `completed` means all outcomes are present and the harness exited normally.

Missing information is JSON null. Source checkouts are required to match pins;
the experiment repo may be dirty/unborn but that is recorded. All saved paths in
the reproducibility command use `<RUN_DIR>`/`<DEPS_DIR>` placeholders to avoid host
directory disclosure. No full environment dump or Ollama Modelfile is collected.

The summarizer supports only schema 1 / `aider-polyglot`, warns and skips other
adapters, and never executes raw code. It regenerates metrics from raw files while
preserving the recorded execution status. In future, a benchmark adapter should
normalize quality/task metrics and a runtime adapter should supply identity and
supported inference metrics; neither should redefine existing metric meanings.

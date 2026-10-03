# Metric definitions

CSV pass rates are fractions in [0, 1], not percentages. Memory columns named
`_mb` use MiB (2²⁰ bytes). Unavailable metrics are null in JSON and empty in CSV.
Zeros are emitted only when actually supported by observations/counts.

| Metric | Definition and caveats |
| --- | --- |
| `task_count` | Number of selected tasks in the saved manifest, not an inferred full-suite size. |
| `passed` / `failed` | Number of nonempty all-boolean `tests_outcomes` records whose last value is true / false, with no exception. |
| `completed_tasks` | Passed + failed. Harness errors and missing/invalid records do not count. |
| `unknown_tasks` | Selected − completed. This is not model failure. |
| `pass_rate` | Passed / selected, only when every selected task has a valid outcome. Otherwise null. |
| Per-language pass rate | Same rule within each language, saved in the run summary JSON. |
| Task `duration_sec` | Monotonic wall time around the upstream task call, including Aider, tests and task overhead. Stored in `.benchmark.timing.json`. |
| Task `aider_duration_sec` | Upstream `duration`, which accumulates Aider call/edit time and excludes unit-test time. Not inference-only time. |
| `total_time_sec` | Monotonic wall time around benchmark `docker run`; includes container start/stop and harness startup, excludes setup/build/preflight and final collection. |
| `avg_time_sec` | Mean task wall duration, only when every selected task has a valid nonnegative duration. Not total wall time divided by count. |
| `memory_used_mb` | `vm_stat` (active + inactive + wired + compressor-occupied pages) × reported page size / 2²⁰. Host-wide approximation, not Activity Monitor's memory-used definition or model allocation. |
| `peak_memory_mb` | Maximum observed memory estimate during periodic polling. Not a continuous peak and not Ollama-only memory. |
| `swap_used_mb` / `peak_swap_mb` | Host-wide `sysctl vm.swapusage` used value / its sampled maximum. Not a change from baseline. |
| `cpu_percent` | 100 − idle from `top -l 1 -n 0`. macOS's reported aggregate observation, not a synchronized interval measurement. |
| `load_1m` | One-minute system load average; not a percentage. |
| `battery_start` / `battery_end` | `pmset -g batt` percentage immediately before/after benchmark. |
| `battery_drop` | Start − end in percentage points, only if endpoints and every available poll say Battery Power. Negative values remain observable; do not clamp. |
| `battery_state`, `power_source` | Native reported battery state and AC/Battery Power label. |
| Tokens/sec | Unsupported: Aider result token counts do not provide Ollama's matching inference durations. Do not divide tokens by task time and call it inference speed. |
| Temperature / watts | Unsupported: no sudo, private Apple API or proprietary dependency is used. |

Sampling defaults to 5 seconds **between completed samples**, so command overhead
adds to the interval. Commands are not atomic; their values have small timing
offsets. Polling adds host overhead and can miss short peaks or brief power-source
changes. Battery percentage is coarse; it is not energy in Wh. Very short runs
may have no useful sampled maximum. Endpoint observations remain in metadata.

Manual collector (Ctrl-C stops it):

```bash
./scripts/collect-stats.sh --output /tmp/llm-stats.csv --interval 5
```

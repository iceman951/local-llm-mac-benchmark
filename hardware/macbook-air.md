# Initial hardware scope

Target: Apple Silicon MacBook Air, **24 GB unified memory**, macOS. Chip generation,
hardware model, OS build and installed software versions are observations, not
hardcoded assumptions. The runner records them for every run:

```bash
make system-info
```

`hw.memsize` is recorded in bytes (24 GiB is 25,769,803,776 bytes). Avoid describing
this whole capacity as model-available memory: macOS, the Docker VM and other
applications share it. Select model size/quantization/context accordingly.

For an article, accompany machine metadata with an experiment note documenting
power mode, AC/battery operation, ambient conditions, cooling/rest period, Docker
Desktop CPU/memory allocation, prior model residency, and background workloads.
Those conditions are not reliably inferred by the current scripts. Native stats
use `sysctl`, `vm_stat`, `top`, and `pmset` without sudo; missing fields stay null.

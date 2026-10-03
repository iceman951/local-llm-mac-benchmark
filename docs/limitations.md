# Limitations

- The initial scope is one Apple Silicon laptop class with 24 GB unified memory.
  Thermal state, charging, power mode, other applications, memory pressure and
  shared CPU/GPU memory affect measurements. There is no causal attribution of
  whole-system resource use to the model alone.
- The benchmark measures an Aider/model/edit-format/test combination. A failing
  task may reflect test infrastructure, formatting, context limits or inference.
  Passing known tests does not establish general correctness or intelligence.
- Three-task smoke runs do not represent the full benchmark or every language.
  Compare identical saved subsets; publish counts and unknown tasks.
- Temperature zero is requested, not a guarantee of deterministic output. Runtime
  changes, model templates, context limits, hardware and floating-point behavior
  can change outputs. The model digest is checked before/after, not every request.
- Host and container Python versions can differ. Replay the saved task manifest;
  a seed alone is not the strongest cross-version reproducibility artifact.
- Source SHAs are pinned. The upstream Dockerfile uses mutable package sources
  and a mutable base tag. Image rebuilding is not bit-for-bit reproducible.
  Preserve the image ID/digest, package inventory, and an external image archive
  if exact tooling is required. A local image ID cannot itself download an image.
- Exercise tooling may download language dependencies at runtime, outside the
  captured Python inventory. Record caches/network conditions and archive any
  additional dependencies needed for a strictly offline replay.
- Docker on macOS adds a Linux VM and shares physical RAM with native Ollama.
  Container limits differ from Docker VM allocation. Swapping/OOM can invalidate
  performance comparisons; both settings must be reported.
- The container can access the network and the local Ollama API. It runs the
  upstream root-based image with reduced capabilities. This is not a hostile-code
  security boundary; do not use sensitive hosts. The writable run directory is
  untrusted output and can be changed by generated code. Review before sharing.
- Hostname is intentionally captured per the requested metadata and may identify
  a person/device. Native hardware collection avoids broad `system_profiler`
  dumps because those include serial numbers/UUIDs. Sandbox restrictions may
  make even harmless `sysctl` fields null; rerun from a normal terminal.
- SIGINT/SIGTERM are handled, but force-kill, host shutdown or disk exhaustion may
  leave metadata marked running or incomplete. Inspect the named Docker container
  and raw files. Summaries can still be regenerated; do not interpret stale state
  as a completed run.
- No token throughput, exact chip temperature, watts or model-only peak memory is
  claimed. Missing fields are never backfilled with estimates.
- First release validation covers local scripts, synthetic temporary fixtures and
  native metadata capture. A real Docker build, Ollama handshake and three-task
  benchmark must be validated on an equipped host before publishing measurements.

# Headroom benchmark: DESIGN ONLY

State: **BLOCKED**, not implemented or executed. Headroom 0.42.0 was proposed upstream,
but this public repository does not independently verify the wheel, its dependencies, CLI or MCP integration.

## Required gates before running Headroom

1. Isolation preflight PASS and container image provenance reviewed.
2. Exact Headroom package and full transitive dependency graph with locked hashes.
3. Connected acquisition stage uses `pip download --require-hashes`, audits wheel inventory.
4. Offline stage uses `pip install --no-index --find-links` with predownloaded wheels and no external network.
5. Explicit authorization for executing the package after review.

## Future metrics (not measured yet)

- Same version and encoding of tokenizer for raw/compact text. Token counts are approximations of model usage.
- Exact seeded facts tested: IDs, numeric values, negations, event order, error codes.
- Recoverability and byte-for-byte recovery checked against SHA-256 originals.
- Repeated trials with median and dispersion for wall time, max RSS, CPU and disk.
- Compare with a plain deterministic filter baseline, not just uncompressed input.
- Document failure cases and lossiness; synthetics do not establish real-world generality.

Do not claim this will compress the current agent's internal context. An independent
artifact-processing tool is not an agent host integration.

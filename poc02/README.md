# PoC 02 — offline preparation, product NOT_RUN

**Verdict: BLOCKED for functional execution.** This is a draft audit/benchmark proposal for Issue #2. No new workflow, package installation, product import, provider call, agent integration or merge is authorized by these files.

## Verified evidence

The merged baseline is `c18076d8ab7ae365d1e0d9c7b4b2b215ac983272`. Run [43103270792](https://github.com/Facu199806/ai-tooling-lab/actions/runs/43103270792), job [130799934106](https://github.com/Facu199806/ai-tooling-lab/actions/runs/43103270792/job/130799934106), concluded success on 2026-11-11. Its 11 defined controls and PREFLIGHT_PASS were independently read in the job log. `audit/preflight-evidence.json` preserves scoped excerpts and the tested Ubuntu image digest. The result establishes only those tests on that container; it does not validate a Python runtime, package compatibility or absolute runner/daemon isolation. No new runs were started for this PR.

Headroom **0.42.0** remains the explicit candidate to keep this experiment comparable with the earlier audit, not a claim that it is the latest or recommended for production. Distribution: `headroom_ai-0.42.0-cp310-abi3-manylinux_2_28_x86_64.whl`, 15,776,655 bytes, SHA-256 `fbb3ceb8f6c3f208edcc3aad43c0e03e0db45636d9d2061525ad0d0a166da146`; Apache-2.0 declared. Upstream source tag previously inspected: v0.42.0, commit `17d38e5699b7d7c69ac6addcd762f39e42dd7f00`. Source-to-wheel reproducible build and independent signing/attestation are **not verified**.

## Distribution audit

Target: CPython 3.12, Linux x86_64, glibc >=2.28. An already installed resolver, uv 0.13.6, resolved only binary distributions against public PyPI using `--only-binary :all:`, no configuration/workspace sources or Python downloads. No build backend, installed dependency or product code ran. Release metadata and wheel archives were read as data with our standard-library tools. Archives were not extracted into Python import paths.

- **68 distributions:** 1 root, 12 direct, 55 transitive. `audit/requirements-target.txt` pins exactly one SHA-256 per selected wheel. No extras such as all/proxy/MCP/ML are selected; the base package nevertheless brings integration SDKs and binaries transitively.
- **107,606,279 bytes** of wheel archives statically inspected. Every selected wheel matched public-index hash, size, package/version metadata and internal RECORD hashes. Unexpected ZIP paths, links, duplicate entries and unrecorded files are rejected. `audit/bundle-verification.json` records the independent second verification.
- **25 ELF files in 19 packages**, including Headroom `_core.abi3.so`, LiteLLM `_native.abi3.so`, ast-grep executables and tokenizers. All inspected ELF headers declare machine 62 (x86_64). `audit/native.json` lists dynamic library dependencies and versioned GLIBC/GLIBCXX symbols. No library was loaded and no ldd or native executable was run. CPU instruction requirements and actual symbol resolution remain untested.
- No `.pth`, `sitecustomize.py` or `usercustomize.py` members detected in this selected set. CLI entry points, provider SDKs and native modules still represent execution surface.
- All packages have a license declaration/classifier in release metadata. **tokenizers 0.23.3 has no identifiable license file in its selected wheel.** This does not mean it is unlicensed; upstream license/NOTICE and redistribution obligations need disposition. Native/vendored dependency notices are not fully adjudicated. `DEPENDENCIES.md` lists declarations, roles, native count and complete wheel hashes.
- A batch query to OSV for all 68 exact versions returned no known vulnerability records. Query, timestamp and response are retained in `audit/osv-query.json`. This is time-bound coverage, not malware detection, a source audit or a guarantee of no vulnerabilities.
- Inventory `Requires-Dist` fields preserve raw conditions/extras; do not treat every raw metadata entry as an active edge. The resolved package set is target-specific. No alternative platform is approved.

Published hash agreement proves identity relative to the registry metadata, not publisher account security or an independent source/binary chain. License declarations and absence of advisories do not certify safety.

## Download stage — network enabled, no package execution

The current task performed static artifact reads solely for audit. A reusable execution bundle is **not yet approved**. A later acquisition must use the reviewed committed manifest; do not resolve fresh versions or trust a new latest tag. No wheels, models or tokenizer data are committed to Git.

Our `acquire.py` default mode reads metadata; its separate download mode fetches only fixed URLs and verifies the audited hashes and RECORD. No installer, build backend or artifact entry point runs. Keep acquisition separate from the execution container, without private files or credentials. Destination should be new/scoped; the tool rejects corrupt existing artifacts rather than replacing them silently.

Prepared future command (requires the later acquisition authorization):

```sh
python3 poc02/acquire.py --lock poc02/audit/requirements-target.txt \
  --output acquisition/wheels --download \
  --approved-manifest poc02/audit/inventory.json
```

For an installer-based acquisition, the equivalent reviewed policy is `pip download --require-hashes --only-binary=:all: --no-deps -r requirements-target.txt`; all 68 pins must be present and target tags explicitly selected. Never use `--no-deps` to omit unreviewed transitive requirements. Our fixed-URL acquisition avoids silently selecting another candidate. Actual compatibility still requires cross-checking against the installer inside the target image. Cache keys and URLs are not evidence of authenticity.

Tokenizer: **tiktoken 0.14.0 / cl100k_base**. `audit/tokenizer-resource.json` pins the public resource URL, SHA-256 and the cache filename SHA-1 of the URL required by tiktoken. The 1,681,126 resource bytes were verified statically without importing tiktoken. SHA-1 here is only a cache lookup key, never the integrity check. The resource and wheel are separate assets and both must be verified before network removal. A missing resource must cause BLOCKED, not a download/fallback.

Build the future readonly `/bundle` with reviewed `inventory.json`, `requirements-target.txt`, `wheels/` and `tokenizer-cache/`. Verify all hashes again immediately before offline installation. Keep wheels and resources out of public artifacts; retain manifests, tests and small synthetic metrics only. Public artifacts/logs are not a suitable place for private data even if retention is short.

## Offline runtime — prepared, not started

The preflight used **Ubuntu without a verified Python/package runtime**. Select and review a digest-pinned Python 3.12 image and its provenance, platform, trusted installer and dynamic libraries. Re-run the approved isolation checks on that exact image and exact mounts **only after new authorization**. Do not reuse a historic PASS as evidence for a materially different runtime.

Use explicit Docker `--network none`, UID/GID 65534, read-only root and inputs, ALL capabilities dropped, no-new-privileges, PID/CPU/memory/disk limits, and no runner workspace, home, Docker socket, provider credentials or host namespaces. `jobs.container.options` cannot supply --network; the existing explicit Docker pattern is appropriate. The host remains network-capable for Actions control/acquisition, so keep the tested process isolated from it.

Use a bounded writable **executable** tmpfs for the installed environment: native libraries cannot reliably load from a noexec filesystem. Restrict writes to that environment, data tmpfs and an output quota. This is a deliberate change from the tiny preflight and needs validation. Suggested initial functional limits: 2 CPU, 2 GiB RAM, 128 PIDs, 512 MiB environment tmpfs and 32 MiB output. These are proposed limits, not observed consumption or guaranteed sufficiency. Root, bundle and scripts remain RO.

`offline_install.sh` is syntax-checked only. It first verifies the wheelhouse, then creates an isolated environment and uses:

```sh
python -I -m pip --isolated install --no-index --find-links=/bundle/wheels \
  --only-binary=:all: --require-hashes --no-compile -r /bundle/requirements-target.txt
```

Installer, ensurepip and the base interpreter are part of the runtime trust review. Installing wheels is not a way to avoid execution risks: native imports and startup hooks can execute on later interpreter startup. Readiness gates therefore precede installation. `pip check` is proposed inside isolation, not performed now. No global install, proxy, hook, MCP, provider SDK call, service or agent configuration is part of this PoC.

HEADROOM_OFFLINE=1 and disabled exporters/model-download options are defense in depth, not a network barrier. Headroom's offline policy has traffic exceptions; no inference client is constructed here. No provider credentials or real model inference are necessary. `gpt-4o` in the adapter is a fixed local counting/configuration label, not a selected paid endpoint.

## Benchmark design — product NOT_RUN

`benchmark.py` imports only our stdlib verifier until its explicit CLI gate. The later product path requires separate authorization and reviewed isolation, supply-chain and tokenizer gates. These flags/files are operator controls, not a sandbox or cryptographic proof; the host must supply the real boundary. No new workflow automatically runs the benchmark.

Four deterministic datasets: long Oracle/ORDS-style logs (rare error/negation/version/order), fictitious Flutter results (failure and skip), long HTTP JSON arrays (429/503/IDs), and edge JSON types/order/Unicode. Critical decimal amounts are strings to preserve exact decimal text; this corpus does not establish arbitrary floating-point fidelity. No live logs, names, private documents or credentials are used.

Compare raw input, deterministic JSON minification / fixed line filter, and Headroom agent/lossless mode with Kompress disabled. The filter is explicitly lossy; its lower token count cannot establish equivalent information. The minifier is checked semantically. System instructions are protected and tool output is eligible (protect_recent=0), so defaults do not accidentally leave the entire fixture protected.

Metrics use the same pinned cl100k_base encoding and actual tokenization for raw, baseline and Headroom; never substitute char/regex counts or `optimize=False` zero counters. Those tokens approximate a fixed encoding, not billed session usage. Report UTF-8 bytes, per-trial hot wall and user/system CPU, median and samples for dispersion, output hashes/determinism, fallback/lossless signal and max RSS. The script labels RSS as cumulative process-lifetime KiB, not per-fixture independent peaks or summed peaks.

Ten hot trials after one excluded warm-up per fixture; repeat the program in three fresh processes. Host separately captures initialization/import wall time and cgroup peak memory/CPU including children/native code. These host/cgroup metrics and three-process aggregation are specified but **not implemented as an execution workflow**. Do not report controller RSS as total container memory.

For logs, product reconstruction must equal the whole original text. For JSON, use Headroom's expand_compacted API when compacted; independently compare recursively typed values and array order, then canonical hashes. Whitespace-equivalent JSON is semantic recovery, not original byte recovery. Separately reopen the preserved original and verify its exact SHA-256; do not use that original to fake successful codec reconstruction. No opaque CCR/dropped-row marker can count as recovered in this agent-mode test. Plain original fallback may pass fidelity but has zero savings. This does not verify an MCP retrieval protocol or automatic session context integration.

## Gates

| Gate | PASS | FAIL | BLOCKED / current |
|---|---|---|---|
| Artifact integrity | All selected bytes, identity and RECORD match | Corruption, unexpected archive path/member | PASS for static bytes; not runtime approval |
| Supply-chain disposition | Provenance, license/vendor notices and native/runtime risks accepted for every asset | Unacceptable origin or license/risk | BLOCKED: no independent source-to-binary/attestation disposition; tokenizers/vendor notices pending |
| Exact runtime isolation | Same reviewed Python image/mounts pass conclusive checks | Observed egress/write/privilege escape | BLOCKED: historic Ubuntu-only preflight does not establish new runtime |
| Tokenizer resource | Encoding/version and local resource hashes match; no fallback | Hash/encoding mismatch | Static resource PASS; runtime NOT_RUN |
| Fidelity | All seeded facts, types, negations and sequence recovered; originals unchanged | Any lost/changed fact or unverifiable codec output | NOT_RUN |
| Utility | Weighted total token reduction >=20%, at least two long fixtures >=10%; no dense-case growth >5%; compare baseline with fidelity labels | Savings below predeclared threshold | NOT_RUN; thresholds are experimental choices |
| Resources | Complete within stated limits with all metrics; no OOM/timeout | Exceeded limits or inconsistent outputs | NOT_RUN |
| Authorization | Explicit new approval for actual runtime/bundle execution | Out-of-scope action | Not granted by this draft |

Weighted reduction is `1 - sum(output tokens) / sum(raw tokens)`, not an unweighted mean of percentages. Fidelity/security failure overrides savings. Passing these synthetic tests would support a limited independent utility, not answer-quality improvement, product adoption, or integration into an agent host.

## Node.js 20 warning

The observed job warning names `actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683` (v4.2.2): its metadata targets Node 20 and the runner forced Node 24. This affects the Actions host step, not Headroom's Python runtime. The run still succeeded; do not erase or retroactively reinterpret its result. GitHub's [official migration notice](https://github.blog/changelog/2025-09-19-deprecation-of-node-20-on-github-actions-runners/) recommends an action release declaring node24. Prepare a separate reviewed SHA update and compatibility run when authorized; this PR does not modify the workflow or enable legacy/unsafe Node opt-outs.

## Inventory, persistence and rollback

Committed: own scripts/docs, exact lock/metadata, hash/native/license inventory, OSV and historic preflight evidence. Not committed: 68 wheels (107.6 MB), tokenizer data (1.68 MB), acquisition/resolver cache or generated product outputs. These local copies are static audit data and no distribution was installed. They may be discarded/re-acquired by reviewed hash. No long-running process, service or runtime configuration is introduced by preparing this branch.

Preparation rollback: close the draft and delete only its experimental branch if rejected; no application/agent state to restore. Future execution rollback: stop/remove only the recorded run's container, remove its dedicated environment/output tmpfs and temporary bundle copies; preserve small signed/hash manifests and results according to retention. Do not delete global caches, unrelated containers, host processes or original evidence. Runner termination is secondary cleanup, not deletion of public logs/code/third-party copies. Public evidence retention proposed one day for artifacts, minimal configured logs; wheels are not redistribution artifacts.

## Remaining blockers and next review

1. Review upstream/registry attestations or explicitly accept the limited publisher-index trust model and source/binary uncertainty for this experiment; byte integrity alone is not sufficient provenance.
2. Resolve tokenizers license-file omission and native/vendored notice disposition for the locked set. Absence of a filename is not an assertion of no license.
3. Review and pin the Python runtime image and installer; validate its dynamic libraries and exact isolation configuration under a later authorization. No new run is requested or launched here.
4. Review these scripts and the package inventory; obtain explicit approval before any install/import/functional run. Headroom remains **NOT_RUN**.

Static findings and 10 tests of our verifier are not a functional PASS. No metric of Headroom compression, latency, resource consumption or answer quality has been measured.

## Sources

- https://github.com/Facu199806/ai-tooling-lab/issues/2
- https://pypi.org/pypi/headroom-ai/0.42.0/json (per-package release URLs retained in inventory)
- https://github.com/headroomlabs-ai/headroom/tree/17d38e5699b7d7c69ac6addcd762f39e42dd7f00
- https://github.com/openai/tiktoken/blob/0.14.0/tiktoken_ext/openai_public.py
- https://api.osv.dev/v1/querybatch
- https://docs.astral.sh/uv/pip/compatibility/

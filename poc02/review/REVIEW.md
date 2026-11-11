# Incremental resolution — PR #3

Date: 2026-11-11. Reference HEAD: `61f117d3212cd5497d40c9694c6102728fd9a4b7`.

**Documentary review supports requesting only the pinned Python preflight. Functional execution remains BLOCKED.** No Headroom/dependency import, installation, workflow dispatch or merge was performed. No wheel/version/hash was changed. The successful historic Ubuntu preflight and original 68-wheel audit remain evidence of their original scope.

| Block | Documentary finding | Experimental disposition | Physical/runtime finding |
|---|---|---|---|
| tokenizers and native notices | Official tag/source license and PyPI declaration concordant; 37 native-wheel notice files recorded | PASS_WITH_LIMITATIONS for internal synthetic evaluation, with redistribution obligations retained | No package executed |
| Native publication provenance | 12 available publication statements have matching subject hashes; 7 endpoints return 404; no cryptographic attestation verification | PASS_WITH_LIMITATIONS for evidence review; bounded trust proposal below is not operator acceptance for package execution | No package executed |
| CPython runtime | Official namespace/catalog and registry digest chain match; four layer hashes verified; ABI/library/installer evidence prepared | PASS for selecting/preparing the exact runtime | BLOCKED / NOT_RUN until a separately authorized Python preflight succeeds |

## 1. License identification

The official `huggingface/tokenizers` annotated tag `v0.23.3` has tag object `9ab7691f497eff905f961aba51a4bb9be3e9555c`, resolving to commit `301277072263fb3830eb66eec7e47adadf76f1dc`. GitHub reports the tag signature as verified; this is GitHub's report, not an independent local signature verification.

At that immutable source commit:

- Root [LICENSE](https://github.com/huggingface/tokenizers/blob/301277072263fb3830eb66eec7e47adadf76f1dc/LICENSE) is Apache License 2.0. Exact fetched bytes match Git blob `261eeb9e9f8b2b4b0d119366dda99c6fd7d35c64`.
- `bindings/python/Cargo.toml` declares Python binding version **0.23.3** and abi3-py310.
- `tokenizers/Cargo.toml` declares the internal Rust crate version **0.23.2** and license Apache-2.0. The patch-version difference is recorded explicitly; it does not establish an artifact/source reproducible-build relationship.
- `bindings/python/pyproject.toml` classifies Apache licensing and dynamically obtains license/version metadata.
- PyPI's [0.23.3 release metadata](https://pypi.org/pypi/tokenizers/0.23.3/json) has the Apache Software License classifier; its license expression field is empty. The selected wheel hash still matches the existing manifest: `376851d22bcf9d650a5c3090bb83e6cf9e895fbf0595369fa4cd43c1f69b5f87`.

The selected wheel's absent license file is a packaging omission, not evidence that the source is unlicensed. The original wheel is preserved unchanged. `licenses/tokenizers-0.23.3-LICENSE` is a supplemental exact upstream text outside the wheel; its SHA-256 and source blob identity are in `tokenizers-license.json`.

### Native notice obligations retained

`native-notices.json` records the paths, byte sizes and SHA-256 of the **37 already included license/NOTICE-related files in the 19 existing native distributions**. Only these existing notice files were read; wheel integrity/resolution was not repeated and the inventory was not regenerated. Declared package licenses do not automatically describe every statically linked Rust/C component.

For this PoC, keep the original wheel files, their included license/NOTICE files, the supplemental tokenizers license and all attributions together in a private execution bundle. No wheel, modified binary, image or combined SDK is approved for publication or redistribution by this review.

Before any redistribution, assess each included license and native/vendor notice: retain required copyright/permission texts (MIT/BSD-family), Apache license and applicable upstream NOTICE/attribution plus change notices for modifications, and any additional terms identified in combined licenses. The runtime image also contains independently licensed Debian/system components; retain the image's existing `/usr/share/doc` notices. Complete static Rust/C dependency attribution would require reliable build material beyond the wheel metadata. This obligation remains attached to redistribution or adoption; it is not a claim of an identified incompatible license in the current internal experiment.

The official Apache text, especially section 4, is the source for its redistribution conditions: https://www.apache.org/licenses/LICENSE-2.0.html . This is a technical disposition for the stated experiment, not blanket license clearance for a product.

## 2. Publication evidence and bounded trust

The existing SHA-256/RECORD and name/version checks remain PASS. They are not reclassified as cryptographic proof of publisher identity or source origin.

The PyPI Integrity API was queried only for the **19 selected native wheel files**, with their unchanged names and hashes. Results, source URLs, response-document hashes, publisher declarations and decoded subject/predicate fields are in `provenance.json`.

| Result | Distributions |
|---|---|
| Attestation documents available; decoded subject digest matches selected wheel | aiohttp, charset-normalizer, frozenlist, headroom-ai, hf-xet, jiter, markupsafe, multidict, propcache, rpds-py, tokenizers, yarl |
| HTTP 404 for this file's provenance | ast-grep-cli, fastuuid, litellm, pydantic-core, pyyaml, regex, tiktoken |

For Headroom the API declares publisher repository `headroomlabs-ai/headroom`, workflow `release.yml`; for tokenizers it declares `huggingface/tokenizers`, workflow `python-release.yml`. These match the expected upstream identities in the static review. All 12 available decoded subject hashes match. Availability, matching hashes and declared identity are **not a signature verification**: certificate chain, transparency-log inclusion and attestation signatures were not independently verified. A 404 denotes missing publication evidence at that endpoint, not a malware finding or proof that the release was published insecurely.

Evidence levels:

1. Artifact integrity: existing whole-file/RECORD hashes PASS.
2. Distribution identity: existing filename and METADATA checks PASS.
3. Publication claims: available for 12/19 with matching subject and plausible declared upstream publisher; absent for 7/19.
4. Independent cryptographic provenance and source-to-binary reproduction: NOT_VERIFIED.

PyPI explicitly requires consumers to extract and verify attestations as appropriate: https://docs.pypi.org/api/integrity/ . No verification tool was installed or executed here.

### Proposed limited risk acceptance — not granted

For one later synthetic/offline benchmark, propose trusting the already frozen PyPI release identities/hashes and available publication claims, with the unsigned/unverified seven-file cases and native build uncertainty explicitly retained. Scope must be a disposable remote runtime, no secrets/private data/providers, no network, no global installs or agent integration, constrained resources and no redistribution/adoption. A different artifact, version, image, data scope or usage invalidates this proposal and requires a new assessment.

The operator has **not accepted this package-execution risk**. Authorization of the next Python-only preflight would not accept it: the preflight mounts no wheelhouse and imports no candidate dependency. The later Headroom benchmark still needs a separate authorization and a recorded decision on these residuals. No independent rebuild is claimed or fabricated.

## 3. Exact official runtime selected

- Catalog: Docker Official Images `docker.io/library/python`, `3.12-slim-bookworm`, catalog source commit `ce195faae0cdca9680fed707a4074f9e41932dc6`.
- Index: `sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df`.
- **Pinned Linux AMD64 image:** `docker.io/library/python@sha256:0f086103b026048cc50cb5da25ec435c023c5241a83fc44daea593377abc61c4`.
- Configuration: `sha256:313cf8f190a1abab00472c1f0c950c10486c22114bcd8aef2a8198fb587a6d18`.
- CPython declared by the image: **3.12.16**, built from the Python release source with ensurepip. Public GPG key/source hash in the Docker build history are build declarations, not a separately verified local source signature.

Registry response bytes were checked against the index, manifest and configuration digests. The index binds the selected manifest to linux/amd64. The four compressed layer bytes were then verified by their manifest SHA-256 and inspected as tar data, without extracting to an executable/import path or starting a container. `runtime-registry.json` and `runtime-filesystem.json` preserve that evidence. Anonymous public-registry pull authorization was held only in memory; no user/provider token is recorded.

Static final filesystem evidence:

- Debian libc6 `2.36-9+deb12u14`, AMD64; the existing native review only observed GLIBC version references up through 2.28.
- libstdc++6 and libgcc-s1 `12.2.0-14+deb12u1`.
- All eight required sonames have paths in the inspected image: loader, libc, libdl, libgcc_s, libm, libpthread, librt, libstdc++.
- Installed pip metadata declares **25.0.1**. Bundled ensurepip wheel `pip-25.0.1-py3-none-any.whl` SHA-256 `c46efd13b6aa8279f33f2864459c8ce587ea6a1a59ee20de055868d8f7688f7f`.
- CPython 3.12 / x86_64 / expected SOABI `cpython-312-x86_64-linux-gnu` is consistent with the locked cp312 and cp310-abi3 wheel target. This is ABI plausibility, not an executed import test.

The registry digest chain proves immutable content under the reviewed namespace/catalog; it is not a claim of independently verified image signing, absence of malicious code, CPU-instruction compatibility or successful dynamic symbol resolution. Those limits remain explicit.

## 4. Prepared runtime preflight, not executed

The existing `.github/workflows/headroom-preflight.yml` is modified **only in this draft branch** to use the pinned Python image. Its identity and single `workflow_dispatch` input remain the same, allowing the existing default-branch registered workflow to be selected with this branch as ref after approval. No new workflow file, trigger, action dependency, install stage or automatic benchmark is introduced. The historical `c18076d...` workflow/script/logs remain immutable, and main is not changed.

Changes: exact image digest allowlist, `library/python` namespace, bounded swap, noexec temporary data mount, one readonly `/runtime.json` mount and a standard-library Python checker after the unchanged historic shell preflight. Existing checkout SHA/Node warning is left intact to keep its migration separate.

The Docker launch retains nonroot UID/GID 65534, `--network none`, readonly root and scripts, dropped capabilities, no-new-privileges, 1 CPU, 256 MiB RAM and 64 PIDs. No wheelhouse, runner home, private files, Docker socket, credentials or agent configuration is mounted. This preflight does not need the writable executable environment required by later package installation; that later configuration requires its own scoped controls.

`scripts/python_runtime_preflight.py` uses only trusted CPython stdlib. It records Python patch version, architecture/SOABI/glibc, installer metadata and ensurepip wheel hash, required system-library paths and version strings, readonly mount flags, UID/caps/seccomp, loopback-only interfaces/no default route, conclusive TCP/UDP-DNS/IPv6 denials, temporary write/read/delete, socket/bundle absence and common sensitive environment names. It does not import pip, bootstrap ensurepip, install wheels, import a candidate distribution or use dlopen on candidate binaries. Symbol strings are compatibility clues, not proof of dynamic loading.

Timeout or connection refusal alone is not accepted as conclusive network denial. IPv6 EAFNOSUPPORT is explicitly limited to unavailability. The container shares kernel/platform trust and is not an absolute sandbox.

The legacy shell `PREFLIGHT_PASS` marker can appear before the Python checks. To accept the new run require **all**: exact approved head and image, job SUCCESS, all new JSON checks true and final **PYTHON_RUNTIME_PREFLIGHT_PASS**. A legacy marker alone is insufficient. Missing metadata/exception yields BLOCKED; observed failed checks yield FAIL. Logs are the evidence; no extra upload action is added.

Local preparation validation: Python AST and three embedded Bash blocks pass syntax checks; 3/3 tests of our new pure/mocked helper logic pass. These tests neither start Docker nor run the actual target preflight. Existing 68-wheel integrity/tests were not repeated.

## 5. Requested next authorization

After reviewing this commit, authorize **one dispatch only** of existing workflow ID `399831335` (`headroom-preflight.yml`), ref `feat/poc02-headroom-offline-audit`, on the approved new HEAD, input `image_digest=sha256:0f086103b026048cc50cb5da25ec435c023c5241a83fc44daea593377abc61c4`.

The registered workflow already exists on main; GitHub supports choosing another branch/ref for a manual run: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow . Verify the branch HEAD immediately before dispatch; if it differs from the approved head, stop. Do not dispatch main with this digest: main retains the historical Ubuntu namespace. No merge is required for this proposed branch-ref test.

This request covers only trusted Python/OS isolation/runtime properties. It does not authorize Headroom, its dependency imports or installation, a provider call, package benchmark, risk acceptance for binaries, or merging the draft.

Overall status remains **BLOCKED for functional Headroom**, with **documentary preparation sufficient to request the Python-only preflight**. A PASS there would close the runtime-preflight blocker within its measured scope; the separate benchmark approval remains required.

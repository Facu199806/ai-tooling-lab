#!/usr/bin/env bash
# PREPARED ONLY. Execute exclusively after new authorization and runtime gates.
# This script is not an isolation mechanism and must never run on the runner host.
set -euo pipefail
[[ "${LAB_EXECUTION_AUTHORIZED:-}" == "YES" ]] || { echo 'BLOCKED: execution not authorized'; exit 2; }
[[ "${LAB_RUNTIME_PREFLIGHT:-}" == "PASS" ]] || { echo 'BLOCKED: target runtime preflight missing'; exit 2; }
[[ "${LAB_SUPPLY_CHAIN_REVIEW:-}" == "PASS" ]] || { echo 'BLOCKED: supply chain review incomplete'; exit 2; }

# Expected readonly mounts: /bundle (manifest, wheelhouse, tokenizer resources)
# and /src/poc02. /labenv is a bounded writable, executable tmpfs: native .so files
# cannot load from a noexec filesystem. /tmp and /output are independently bounded.
python3 -I /src/poc02/verify_bundle.py /bundle/inventory.json /bundle/wheels /output/bundle-verification.json
python3 -I -m venv /labenv/venv
/labenv/venv/bin/python -I -m pip --isolated install \
  --no-index --find-links=/bundle/wheels --only-binary=:all: \
  --require-hashes --no-compile -r /bundle/requirements-target.txt
/labenv/venv/bin/python -I -m pip check
echo 'Installation finished inside approved offline runtime. Benchmark requires its separate explicit gate.'

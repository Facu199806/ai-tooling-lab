# Remote isolation preflight

## Scope and expected outputs

| Check | Expected |
| --- | --- |
| UID | Non-root |
| Root filesystem | Mount flags include `ro`; write denied |
| Mounted script directory | Mount flags include `ro`; write denied |
| Temporary filesystem | Mount flags include `rw`; write + verify + delete succeed |
| Docker socket | Absent |
| Effective capabilities | Zero |
| `NoNewPrivs` | Enabled |
| TCP egress | Denied |
| DNS resolution | Denied |
| Common secret environment names | Absent |
| Final marker | `PREFLIGHT_PASS` |

Status initially **NOT_RUN**. Any unexpected success on a negative test must emit FAIL and
terminate the workflow nonzero. A PASS does not mean the image, host or tool is intrinsically safe.

Workflow uses Ubuntu 24.04 runner, pinned checkout action, manual dispatch only, and a digest
supplied at dispatch. Before launch, manually audit that OCI digest, platform and image provenance.
No Headroom wheel, CLI, library or MCP server runs at this stage.

No artifacts are uploaded; evidence remains in workflow logs under GitHub's retention settings.
Do not post real data or private files into the public repository or run parameters.

## GitHub Actions release gate

GitHub only accepts `workflow_dispatch` events for workflows present on the default
branch. Therefore the draft PR must be reviewed and merged before its first manual run
can be requested. Merging this PR **does not** automatically start the workflow.
A manual run still requires separate operator approval and a vetted OCI image digest.

The preflight checks read-only mount flags as well as write denials, because denied
writes from a non-root user alone do not prove a mount is read-only.

No Docker command, workflow dispatch or Headroom execution was carried out during preparation.

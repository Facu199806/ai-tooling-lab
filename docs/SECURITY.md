# Security and scope

Public-only synthetic laboratory. No private repositories are to be cloned, mounted, referenced in logs, or used as data sources.

## Current authorization

- Preparing an experimental branch, files and draft PR: allowed.
- Running GitHub Actions, running Headroom, fetching its dependencies or activating MCP: **NOT AUTHORIZED**.
- The workflow has *only* a manual trigger and does not execute Headroom.
- No accounts, access tokens, third-party provider APIs or secrets belong in this repository.

## Isolation model

The GitHub-hosted runner can access the Internet and uses a daemon capable of pulling images.
The test container is launched with `--network none`, non-root UID, read-only root,
read-only script bind mount, dropped capabilities and `no-new-privileges`.
The container does not have Docker socket access, and runs with constrained resources.

This does **not** prove full isolation of the runner, Docker daemon or the GitHub infrastructure.
The preflight measures only specific properties from inside the container. Retain an explicit
threat model and avoid execution of untrusted code until image/dependency provenance is reviewed.

## Supply chain gates

- GitHub checkout action pinned to a full commit SHA.
- Container digest is supplied manually; verify its publisher, signature/provenance and expected
  platform before approving a run. The workflow validates digest syntax, not provenance.
- Do not add network-enabled `pip install` into the offline container.
- A future Headroom PoC must use a separate connected download stage with locked dependency
  graph and verified hashes; offline execution must use only predownloaded wheels.
- No `pull_request_target`, no automatic PR/fork triggers, no deployment steps.

## Rollback

Close the draft PR and delete its experimental branch if the work is rejected. No running
processes or packages are expected from preparing the branch. If the preflight is eventually
executed, the container uses `--rm`; additionally verify the workflow run, logs, artifacts,
and runner completion. Public Git history and workflow logs can persist after branch deletion.

#!/usr/bin/env bash
# Standalone Ubuntu 24.04 preflight. No dependency installation.
set -euo pipefail
export LC_ALL=C

pass() { printf 'PASS %s\n' "$1"; }
fail() { printf 'FAIL %s\n' "$1" >&2; exit 1; }

uid="$(id -u)"
[[ "$uid" != "0" ]] || fail "non-root"
pass "non-root: uid=$uid"

[[ "${LAB_CANARY:-}" == "SYNTHETIC_ONLY" ]] || fail "explicit synthetic environment marker"
pass "synthetic environment marker"

# Verify mount flags. A non-root user may be unable to write even to an RW filesystem.
root_opts="$(awk '$5 == "/" { print $6 }' /proc/self/mountinfo)"
[[ -n "$root_opts" && ",$root_opts," == *,ro,* ]] || fail "root mount is not read-only: $root_opts"
if ( printf 'probe\n' > /etc/aitooling-write-canary ) 2>/dev/null; then
  fail "root filesystem unexpectedly writable"
fi
pass "root mount read-only (mount flags and denied write)"

work_opts="$(awk '$5 == "/work" { print $6 }' /proc/self/mountinfo)"
[[ -n "$work_opts" && ",$work_opts," == *,ro,* ]] || fail "script bind mount is not read-only: $work_opts"
if ( printf 'probe\n' > /work/aitooling-write-canary ) 2>/dev/null; then
  fail "source bind mount unexpectedly writable"
fi
pass "script bind mount read-only (mount flags and denied write)"

tmp_opts="$(awk '$5 == "/tmp" { print $6 }' /proc/self/mountinfo)"
[[ -n "$tmp_opts" && ",$tmp_opts," == *,rw,* ]] || fail "tmpfs is not writable by mount flags: $tmp_opts"

printf 'synthetic\n' > /tmp/aitooling-tmp-canary || fail "tmpfs not writable"
[[ "$(cat /tmp/aitooling-tmp-canary)" == "synthetic" ]] || fail "tmpfs verification"
rm /tmp/aitooling-tmp-canary
pass "tmpfs writable"

[[ ! -S /var/run/docker.sock ]] || fail "Docker socket exposed"
pass "Docker socket absent"

cap_eff="$(awk '/^CapEff:/{print $2}' /proc/self/status)"
[[ "$cap_eff" =~ ^0+$ ]] || fail "Linux capabilities remain effective: $cap_eff"
pass "effective capabilities zero"

no_new_privs="$(awk '/^NoNewPrivs:/{print $2}' /proc/self/status)"
[[ "$no_new_privs" == "1" ]] || fail "no-new-privileges is disabled"
pass "no-new-privileges active"

# Network tests are fail-closed. A connection that succeeds means isolation failed.
if timeout 4 bash -c 'exec 3<>/dev/tcp/1.1.1.1/443' >/dev/null 2>&1; then
  fail "TCP egress unexpectedly possible"
fi
pass "TCP egress denied"

if getent hosts example.com >/dev/null 2>&1; then
  fail "DNS resolution unexpectedly possible"
fi
pass "DNS resolution denied"

# Check no inherited tokens with common sensitive environment variable names.
while IFS='=' read -r key _; do
  case "$key" in
    GITHUB_TOKEN|GH_TOKEN|AWS_*|AZURE_*|OPENAI_*|ANTHROPIC_*|*_API_KEY|*_SECRET|*_PASSWORD)
      fail "unexpected potentially sensitive environment variable: $key" ;;
  esac
done < <(env)
pass "common sensitive environment names absent"

printf 'PREFLIGHT_PASS\n'

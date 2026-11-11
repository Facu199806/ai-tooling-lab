#!/usr/bin/env python3
"""Only trusted CPython stdlib. Do not import any candidate distribution.

Prepared for the pinned runtime; never run on the operator machine or here.
Run after the existing shell isolation preflight, with /runtime.json readonly.
"""
import errno
import hashlib
import importlib.metadata
import json
import os
import pathlib
import platform
import re
import socket
import sys
import sysconfig


def version_at_least(value, minimum):
    match = re.search(r'(\d+)\.(\d+)', value or '')
    return bool(match) and tuple(map(int, match.groups())) >= tuple(minimum)


def readonly_mount(mountinfo, destination):
    return any(len(fields := line.split()) > 6 and fields[4] == destination and 'ro' in fields[5].split(',') for line in mountinfo.splitlines())


def denied_connect(address, family=socket.AF_INET, udp=False):
    try:
        with socket.socket(family, socket.SOCK_DGRAM if udp else socket.SOCK_STREAM) as s:
            s.settimeout(2)
            if udp:
                s.sendto(b'SYNTHETIC_PREFLIGHT_ONLY', address)
            else:
                s.connect(address)
        return False, 'UNEXPECTED_SUCCESS'
    except OSError as e:
        # Timeout/refused/missing executable do not count as conclusive denial.
        return e.errno in {errno.ENETUNREACH, errno.EHOSTUNREACH, errno.EACCES, errno.EPERM, errno.EAFNOSUPPORT}, str(e.errno)


def main():
    spec = json.loads(pathlib.Path('/runtime.json').read_text())
    checks = {}; details = {}
    checks['python_patch_version'] = list(sys.version_info[:3]) == spec['python']
    checks['amd64_64bit'] = platform.machine() == 'x86_64' and sys.maxsize > 2**32
    checks['soabi'] = sysconfig.get_config_var('SOABI') == spec['soabi']
    libc = os.confstr('CS_GNU_LIBC_VERSION')
    checks['glibc_floor'] = version_at_least(libc, spec['glibc_min'])
    details['python'] = platform.python_version(); details['soabi'] = sysconfig.get_config_var('SOABI'); details['libc'] = libc
    # Read installer metadata and bundled wheel bytes, do not import/bootstrap pip.
    checks['pip_metadata'] = importlib.metadata.version('pip') == spec['pip_version']
    checks['ensurepip_integrity'] = hashlib.sha256(pathlib.Path(spec['ensurepip_wheel_path']).read_bytes()).hexdigest() == spec['ensurepip_wheel_sha256']
    roots = [pathlib.Path(p) for p in ['/lib/x86_64-linux-gnu', '/usr/lib/x86_64-linux-gnu', '/lib64']]
    libraries = {s: next((p / s for p in roots if (p / s).is_file()), None) for s in spec['required_sonames']}
    checks['system_library_paths'] = all(libraries.values())
    details['library_paths'] = {k: str(v) if v else None for k, v in libraries.items()}
    libc_bytes = libraries['libc.so.6'].read_bytes() if libraries.get('libc.so.6') else b''
    cpp_bytes = libraries['libstdc++.so.6'].read_bytes() if libraries.get('libstdc++.so.6') else b''
    checks['glibc_version_strings'] = all(x.encode() + b'\0' in libc_bytes for x in spec['required_glibc_symbols'])
    checks['glibcxx_version_strings'] = all(x.encode() + b'\0' in cpp_bytes for x in spec['required_glibcxx_symbols'])
    # Strings/paths are static compatibility clues, not dlopen of third-party ELF.
    mountinfo = pathlib.Path('/proc/self/mountinfo').read_text()
    for destination in ['/', '/work', '/runtime.json']:
        checks['readonly_' + destination] = readonly_mount(mountinfo, destination)
    fields = dict(line.split(':', 1) for line in pathlib.Path('/proc/self/status').read_text().splitlines() if ':' in line)
    checks['nonroot'] = os.getuid() == 65534
    checks['caps_zero'] = int(fields['CapEff'].strip(), 16) == 0
    checks['no_new_privileges'] = fields['NoNewPrivs'].strip() == '1'
    checks['seccomp'] = fields['Seccomp'].strip() == '2'
    checks['loopback_only'] = sorted(os.listdir('/sys/class/net')) == ['lo']
    checks['no_ipv4_default_route'] = not any(line.split()[1:2] == ['00000000'] for line in pathlib.Path('/proc/net/route').read_text().splitlines()[1:])
    for name, addr, family, udp in [('tcp4', ('1.1.1.1', 443), socket.AF_INET, False),
                                    ('udp_dns', ('1.1.1.1', 53), socket.AF_INET, True),
                                    ('tcp6', ('2606:4700:4700::1111', 443), socket.AF_INET6, False)]:
        checks[name], details[name + '_errno'] = denied_connect(addr, family, udp)
    checks['no_docker_socket'] = not pathlib.Path('/var/run/docker.sock').exists()
    checks['no_bundle_mounted'] = not pathlib.Path('/bundle').exists()
    tmp = pathlib.Path('/tmp/python-runtime-canary')
    tmp.write_text('SYNTHETIC_ONLY'); checks['tmp_rw'] = tmp.read_text() == 'SYNTHETIC_ONLY'; tmp.unlink()
    checks['common_credential_names_absent'] = not any(re.match(r'^(GITHUB_TOKEN|GH_TOKEN|AWS_|AZURE_|OPENAI_|ANTHROPIC_)', k) or re.search(r'(_API_KEY|_SECRET|_PASSWORD)$', k) for k in os.environ)
    # Version metadata inspection does not import a distribution.
    forbidden = {'headroom', 'tiktoken', 'litellm', 'tokenizers', 'pydantic', 'requests', 'pip'}
    checks['no_product_dependency_imports'] = not any(n.split('.')[0] in forbidden for n in sys.modules)
    result = {'status': 'PASS' if all(checks.values()) else 'FAIL', 'scope': 'trusted Python runtime preflight only',
              'headroom': 'NOT_RUN', 'checks': checks, 'details': details,
              'limitations': ['No dependency/native wheel imported or installed.', 'Symbol strings do not prove dynamic loading or CPU instruction compatibility.',
                              'Container/kernel/daemon are not absolute isolation.', 'IPv6 EAFNOSUPPORT denotes unavailability, not a tested reachable IPv6 route.']}
    print(json.dumps(result, sort_keys=True))
    print('PYTHON_RUNTIME_PREFLIGHT_PASS' if result['status'] == 'PASS' else 'PYTHON_RUNTIME_PREFLIGHT_FAIL')
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, importlib.metadata.PackageNotFoundError) as error:
        print(json.dumps({'status': 'BLOCKED', 'error': type(error).__name__, 'headroom': 'NOT_RUN'}))
        raise SystemExit(2)

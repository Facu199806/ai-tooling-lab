"""Stdlib-only static acquisition; never install/import inspected packages.

Default: release metadata and candidate wheel manifest. --download is a separate
future acquisition step. Candidate filename matching is not a replacement for
installer compatibility validation in the approved target image.
"""
import argparse
import base64
import concurrent.futures
import csv
import email
import hashlib
import io
import json
import pathlib
import re
import urllib.parse
import urllib.request
import zipfile


def approved_url(url):
    p = urllib.parse.urlsplit(url)
    return p.scheme == 'https' and p.hostname in {'pypi.org', 'files.pythonhosted.org'} and p.port in (None, 443) and p.username is None and p.password is None


class ApprovedRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not approved_url(newurl):
            raise ValueError('Unexpected redirect destination')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def get(url):
    if not approved_url(url):
        raise ValueError('Non-approved distribution host')
    with urllib.request.build_opener(ApprovedRedirect()).open(url, timeout=30) as response:
        if urllib.parse.urlsplit(response.url).hostname not in {'pypi.org', 'files.pythonhosted.org'}:
            raise ValueError('Unexpected redirect')
        data = response.read(100_000_001)
        if len(data) > 100_000_000:
            raise ValueError('Artifact exceeds transfer budget')
        return data


def eligible(filename):
    if not filename.endswith('.whl'):
        return False
    py, abi, platform = filename[:-4].rsplit('-', 3)[1:]
    if platform == 'any':
        return 'py3' in py.split('.') and abi == 'none'
    if 'x86_64' not in platform or 'musllinux' in platform or not 'manylinux' in platform:
        return False
    levels = re.findall(r'manylinux_2_(\d+)_x86_64', platform)
    if levels and not any(int(level) <= 28 for level in levels):
        return False
    if not levels and not any(x in platform for x in ['manylinux1_', 'manylinux2010_', 'manylinux2014_']):
        return False
    if py == 'cp312' and abi in {'cp312', 'abi3', 'none'}:
        return True
    if 'py3' in py.split('.') and abi == 'none':
        return True
    return abi == 'abi3' and py.startswith('cp3') and 2 <= int(py[3:]) <= 12


def inspect_wheel(data, expected_name, expected_version):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = z.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate ZIP entries')
        if any(n.startswith('/') or '..' in pathlib.PurePosixPath(n).parts or '\\' in n for n in names):
            raise ValueError('Unsafe ZIP path')
        if sum(i.file_size for i in z.infolist()) > 512_000_000:
            raise ValueError('Uncompressed artifact exceeds audit budget')
        if any((i.external_attr >> 16) & 0o170000 == 0o120000 for i in z.infolist()):
            raise ValueError('Symlink entry requires separate review')
        metadata = [n for n in names if n.endswith('.dist-info/METADATA')]
        records = [n for n in names if n.endswith('.dist-info/RECORD')]
        if len(metadata) != 1 or len(records) != 1:
            raise ValueError('Ambiguous wheel metadata')
        m = email.message_from_bytes(z.read(metadata[0]))
        norm = lambda s: re.sub(r'[-_.]+', '-', s.lower())
        if norm(m['Name']) != norm(expected_name) or m['Version'] != expected_version:
            raise ValueError('Distribution identity mismatch')
        verified = set()
        native_magic = []
        for name, digest, size in csv.reader(io.StringIO(z.read(records[0]).decode())):
            if name in verified:
                raise ValueError('Duplicate RECORD entry')
            verified.add(name)
            if name not in names:
                raise ValueError('RECORD references missing member')
            if not digest:
                if name != records[0] and not name.endswith(('.jws', '.p7s')):
                    raise ValueError('Unexpected unhashed member')
                continue
            algorithm, want = digest.split('=', 1)
            if algorithm not in {'sha256', 'sha384', 'sha512'}:
                raise ValueError('Weak/unsupported RECORD hash')
            blob = z.read(name)
            if blob.startswith((b'\x7fELF', b'MZ', b'\xcf\xfa\xed\xfe', b'\xfe\xed\xfa\xcf')):
                native_magic.append(name)
            got = base64.urlsafe_b64encode(hashlib.new(algorithm, blob).digest()).decode().rstrip('=')
            if got != want or str(len(blob)) != size:
                raise ValueError('RECORD integrity mismatch')
        if any(n not in verified for n in names if not n.endswith('/') and not n.endswith(('.jws', '.p7s'))):
            raise ValueError('Unrecorded wheel member')
        return {'record_verified': True,
                'native_magic_members': native_magic,
                'native_members': [n for n in names if n.endswith(('.so', '.pyd', '.dll', '.dylib')) or '/bin/' in n or n.endswith('.exe')],
                'startup_members': [n for n in names if n.endswith('.pth') or n.endswith(('sitecustomize.py', 'usercustomize.py'))],
                'entry_points': [n for n in names if n.endswith('entry_points.txt')],
                'license_files': [n for n in names if re.search(r'(?i)(license|copying|notice)', n)],
                'requires_dist': m.get_all('Requires-Dist', []),
                'license_expression': m.get('License-Expression'),
                'license_declared': (m.get('License') or '')[:200]}


def describe(pair):
    name, version = pair
    url = f'https://pypi.org/pypi/{name}/{version}/json'
    release = json.loads(get(url))
    candidates = sorted((a for a in release['urls'] if eligible(a['filename']) and not a.get('yanked')), key=lambda a: a['filename'])
    if not candidates:
        raise ValueError(f'No target candidate wheel for {name}=={version}')
    chosen = candidates[0]
    info = release['info']
    return {'name': name, 'version': version, 'purl': f'pkg:pypi/{name}@{version}', 'metadata_url': url,
            'requires_dist': info.get('requires_dist') or [], 'requires_python': info.get('requires_python'),
            'license_expression': info.get('license_expression'), 'license_declared': (info.get('license') or '')[:200],
            'license_classifiers': [c for c in info.get('classifiers', []) if c.startswith('License ::')],
            'artifact': {k: chosen[k] for k in ['filename', 'url', 'size', 'upload_time_iso_8601']},
            'sha256': chosen['digests']['sha256'], 'bytes_verified': False,
            'native_expected_from_tag': not chosen['filename'].endswith('-none-any.whl'),
            'candidate_wheels': [a['filename'] for a in candidates]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--lock', type=pathlib.Path, required=True)
    p.add_argument('--output', type=pathlib.Path, required=True)
    p.add_argument('--download', action='store_true')
    p.add_argument('--approved-manifest', type=pathlib.Path)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    if args.download:
        if args.approved_manifest is None:
            p.error('--download requires a previously reviewed --approved-manifest; no fresh resolution')
        inventory = json.loads(args.approved_manifest.read_text())
        packages = inventory['packages']
    else:
        pairs = re.findall(r'^([A-Za-z0-9_.-]+)==([^\s;\\]+)', args.lock.read_text(), re.M)
        if not pairs or len(pairs) != len({n for n, _ in pairs}):
            raise ValueError('Invalid candidate lock')
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            packages = list(pool.map(describe, pairs))
        inventory = {'status': 'CANDIDATE_NOT_APPROVED', 'target': 'CPython 3.12 / Linux x86_64 / glibc >=2.28',
                     'root': 'headroom-ai==0.42.0', 'packages': packages,
                     'limitations': ['Release metadata is not independently attested.', 'Wheel bytes and contents not verified in metadata mode.',
                                     'Filename candidate matching requires target installer cross-check.', 'Vulnerability and license disposition require review.']}
    if args.download:
        def inspect_item(item):
            filename = item['artifact']['filename']
            if pathlib.Path(filename).name != filename or not filename.endswith('.whl'):
                raise ValueError('Unsafe artifact basename')
            target = args.output / filename
            data = target.read_bytes() if target.is_file() else get(item['artifact']['url'])
            if len(data) != item['artifact']['size'] or hashlib.sha256(data).hexdigest() != item['sha256']:
                raise ValueError('Artifact hash/size mismatch')
            item['inspection'] = inspect_wheel(data, item['name'], item['version'])
            item['bytes_verified'] = True
            target.write_bytes(data)
            return item
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            packages = list(pool.map(inspect_item, packages))
        inventory['packages'] = packages
    (args.output / 'inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
    (args.output / 'requirements-target.txt').write_text(''.join(f"{i['name']}=={i['version']} --hash=sha256:{i['sha256']}\n" for i in packages))
    print(json.dumps({'packages': len(packages), 'downloaded': args.download, 'headroom_executed': False}))


if __name__ == '__main__':
    main()

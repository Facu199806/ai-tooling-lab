"""Verify wheel bytes/RECORD without importing packages; never approve runtime."""
import argparse
import hashlib
import json
import pathlib
import sys
# Explicitly add only our readonly source directory, including under python -I.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from acquire import inspect_wheel


def verify(manifest, directory):
    results = []
    expected_files = set()
    for item in manifest['packages']:
        name = item['artifact']['filename']
        if pathlib.Path(name).name != name or not name.endswith('.whl'):
            raise ValueError('Unsafe artifact basename')
        expected_files.add(name)
        p = directory / name
        if p.is_symlink() or not p.is_file():
            raise ValueError('Missing or linked artifact')
        b = p.read_bytes()
        if len(b) != item['artifact']['size'] or hashlib.sha256(b).hexdigest() != item['sha256']:
            raise ValueError('Wheel bytes differ from reviewed manifest')
        report = inspect_wheel(b, item['name'], item['version'])
        results.append({'name': item['name'], 'sha256': item['sha256'], 'inspection': report})
    if {p.name for p in directory.glob('*.whl')} != expected_files:
        raise ValueError('Unexpected/missing wheel in bundle')
    allowed = expected_files | {'inventory.json', 'requirements-target.txt'}
    if any(p.name not in allowed or p.is_symlink() or not p.is_file() for p in directory.iterdir()):
        raise ValueError('Unexpected file/directory in wheelhouse')
    return {'integrity': 'PASS', 'runtime_approval': 'NOT_GRANTED', 'packages': results}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('manifest', type=pathlib.Path)
    p.add_argument('wheels', type=pathlib.Path)
    p.add_argument('report', type=pathlib.Path)
    args = p.parse_args()
    report = verify(json.loads(args.manifest.read_text()), args.wheels)
    args.report.write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__': main()

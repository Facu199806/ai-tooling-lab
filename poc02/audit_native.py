"""Inspect ELF headers/DT_NEEDED statically, never use ldd or load a library."""
import argparse
import json
import pathlib
import re
import struct
import zipfile


def elf_info(b):
    if not b.startswith(b'\x7fELF') or b[4] != 2:
        return {'status': 'BLOCKED', 'reason': 'Only ELF64 statically parsed'}
    endian = '<' if b[5] == 1 else '>'
    header = struct.unpack_from(endian + '16sHHIQQQIHHHHHH', b)
    offset, size, count = header[6], header[11], header[12]
    if count > 10000 or size < 64 or offset + size * count > len(b):
        raise ValueError('ELF section bounds')
    sections = [struct.unpack_from(endian + 'IIQQQQIIQQ', b, offset + i * size) for i in range(count)]
    needed = []
    for section in sections:
        if section[1] != 6:
            continue
        strings = sections[section[6]]
        table = b[strings[4]:strings[4] + strings[5]]
        for at in range(section[4], section[4] + section[5], 16):
            tag, value = struct.unpack_from(endian + 'qQ', b, at)
            if tag == 1:
                needed.append(table[value:].split(b'\0', 1)[0].decode('ascii'))
    symbols = sorted({x.decode() for x in re.findall(rb'GLIBC(?:XX)?_[0-9.]+', b)})
    return {'status': 'STATIC_ONLY', 'elf_machine': header[2], 'machine_expected_x86_64': header[2] == 62,
            'needed_libraries': sorted(set(needed)), 'versioned_symbols': symbols,
            'limitation': 'No instruction-set, symbol-resolution, source-to-binary, or runtime compatibility proof'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('manifest', type=pathlib.Path)
    p.add_argument('wheels', type=pathlib.Path)
    p.add_argument('output', type=pathlib.Path)
    args = p.parse_args()
    results = []
    for item in json.loads(args.manifest.read_text())['packages']:
        with zipfile.ZipFile(args.wheels / item['artifact']['filename']) as z:
            for member in item['inspection']['native_magic_members']:
                results.append({'package': item['name'], 'member': member, **elf_info(z.read(member))})
    args.output.write_text(json.dumps(results, indent=2) + '\n')


if __name__ == '__main__': main()

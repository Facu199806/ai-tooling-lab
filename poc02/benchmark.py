"""Prepared benchmark. Stdlib imports only until explicit execution gate.

No provider calls. Headroom/tiktoken must already exist in the approved offline
runtime. This program is NOT a sandbox; the host must enforce isolation first.
"""
import argparse
import copy
import hashlib
import json
import os
import pathlib
import resource
import statistics
import time


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def typed_equal(a, b):
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(typed_equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(typed_equal(x, y) for x, y in zip(a, b))
    return a == b


def cases():
    logs = [f'2026-01-01T00:{i // 60:02}:{i % 60:02}Z INFO SYN-{i:04} rows=17 status=OK' for i in range(600)]
    logs[37] = '2026-01-01T00:00:37Z ERROR SYN-RARE-037 ORA-00600 fictional_only NO COMMIT amount=-0.01'
    logs += ['2026-01-01T00:10:00Z ORDS SYN-REQ-007 HTTP=409 expected_version=7 actual_version=8',
             '2026-01-01T00:10:01Z WARN SYN-REQ-007 NO reintentar antes de consultar',
             '2026-01-01T00:10:02Z INFO SYN-REQ-007 ROLLBACK confirmado despues del rechazo']
    yield 'oracle_ords', '\n'.join(logs) + '\n', False
    tests = [f'PASS synthetic_widget_{i:04}' for i in range(500)]
    tests += ['FAIL synthetic_boundary expected=1000 actual=1001 UTF-16',
              'SKIPPED synthetic_physical NO validado en dispositivo',
              'SUMMARY passed=500 failed=1 skipped=1 total=502']
    yield 'flutter', '\n'.join(tests) + '\n', False
    records = [{'seq': i, 'id': f'SYN-HTTP-{i:04}', 'status': 200, 'committed': False,
                'amount': '-0.01', 'value': None, 'note': 'NO reintentar antes de consultar'} for i in range(1000)]
    records[37]['status'] = 429
    records[37]['retry_after'] = 17
    records[999]['status'] = 503
    yield 'http_json', json.dumps(records, ensure_ascii=False, indent=2) + '\n', True
    edge = [{'id': 'SYN-0001', 'value': False}, {'id': 'SYN-0010', 'value': 0},
            {'id': 'SYN-NULL', 'value': None}, {'id': 'SYN-MISSING'},
            {'id': 'SYN-EMPTY', 'value': ''}, {'id': 'SYN-TEXT', 'value': 'null'},
            {'id': 'SYN-UNICODE', 'value': 'ñ — 😀 , " \\ \n'},
            {'id': 'SYN-ORDER', 'events': ['send', 'timeout', 'query', 'confirm'], 'amount': '-0.01'}]
    yield 'edge_types_order', json.dumps(edge, ensure_ascii=False, indent=2) + '\n', True


def filter_baseline(raw, is_json):
    if is_json:
        return canonical(json.loads(raw)), 'json_minification_lossless_semantically'
    keep = ('ERROR', 'WARN', 'FAIL', 'SKIPPED', 'SUMMARY', 'ROLLBACK', 'NO ', 'HTTP=409')
    return '\n'.join(line for line in raw.splitlines() if any(k in line for k in keep)) + '\n', 'line_filter_lossy'


def recover(raw, compact, is_json, expand, is_compacted):
    if not is_json:
        return compact == raw, compact.encode() == raw.encode()
    # Do not silently recover from raw/original to certify the product codec.
    if is_compacted(compact):
        reconstructed = expand(compact)
    else:
        try:
            reconstructed = json.loads(compact)
        except ValueError:
            return False, False
    original = json.loads(raw)
    if not typed_equal(original, reconstructed):
        return False, False
    # Semantic JSON recovery is distinct from original whitespace/byte recovery.
    return True, digest(canonical(original).encode()) == digest(canonical(reconstructed).encode())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute-after-approval', action='store_true')
    p.add_argument('--gate', type=pathlib.Path, required=True)
    p.add_argument('--output', type=pathlib.Path, required=True)
    args = p.parse_args()
    gate = json.loads(args.gate.read_text())
    if not args.execute_after_approval or any(gate.get(k) != 'PASS' for k in ['isolation', 'supply_chain', 'tokenizer_resource']):
        raise SystemExit('BLOCKED: explicit authorization and reviewed runtime/bundle gates required')
    os.environ['HEADROOM_OFFLINE'] = '1'
    os.environ['LITELLM_LOCAL_MODEL_COST_MAP'] = 'True'
    os.environ['OTEL_SDK_DISABLED'] = 'true'
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    if not os.environ.get('TIKTOKEN_CACHE_DIR'):
        raise SystemExit('BLOCKED: verified tokenizer cache path required')
    resource_spec = json.loads((pathlib.Path(__file__).resolve().parent / 'audit/tokenizer-resource.json').read_text())
    resource_path = pathlib.Path(os.environ['TIKTOKEN_CACHE_DIR']) / resource_spec['cache_filename_sha1_url']
    if not resource_path.is_file() or digest(resource_path.read_bytes()) != resource_spec['sha256']:
        raise SystemExit('BLOCKED: tokenizer resource missing or changed')
    # This path is prepared only; imports must occur exclusively inside isolation.
    import importlib.metadata
    if importlib.metadata.version('headroom-ai') != '0.42.0' or importlib.metadata.version('tiktoken') != '0.14.0':
        raise SystemExit('BLOCKED: runtime package version mismatch')
    import tiktoken
    from headroom import compress, expand_compacted, is_compacted
    encoding = tiktoken.get_encoding('cl100k_base')
    args.output.mkdir(parents=True, exist_ok=False)
    results = []
    for name, raw, is_json in cases():
        before_hash = digest(raw.encode())
        original_path = args.output / (name + '.original.txt')
        original_path.write_bytes(raw.encode())
        original_path.chmod(0o444)
        baseline, baseline_kind = filter_baseline(raw, is_json)
        (args.output / (name + '.baseline.txt')).write_text(baseline)
        messages = [{'role': 'user', 'content': 'Inspect the synthetic results without changing facts.'},
                    {'role': 'assistant', 'content': None, 'tool_calls': [{'id': 'SYN-CALL', 'type': 'function', 'function': {'name': 'synthetic', 'arguments': '{}'}}]},
                    {'role': 'tool', 'tool_call_id': 'SYN-CALL', 'content': raw}]
        samples = []
        baseline_samples = []
        outputs = []
        # One warm-up excluded from hot measurements. Caller repeats whole program
        # in three fresh processes; initialization is measured separately by host.
        for trial in range(11):
            baseline_cpu0 = resource.getrusage(resource.RUSAGE_SELF)
            baseline_start = time.perf_counter_ns()
            baseline, baseline_kind = filter_baseline(raw, is_json)
            baseline_elapsed = time.perf_counter_ns() - baseline_start
            baseline_cpu1 = resource.getrusage(resource.RUSAGE_SELF)
            if trial:
                baseline_samples.append({'wall_ns': baseline_elapsed,
                                         'cpu_user_seconds': baseline_cpu1.ru_utime - baseline_cpu0.ru_utime,
                                         'cpu_system_seconds': baseline_cpu1.ru_stime - baseline_cpu0.ru_stime})
            cpu0 = resource.getrusage(resource.RUSAGE_SELF)
            start = time.perf_counter_ns()
            result = compress(copy.deepcopy(messages), model='gpt-4o', mode='agent',
                              protect_recent=0, compress_system_messages=False,
                              kompress_model='disabled', verify_lossless=True, diagnostics=True)
            elapsed = time.perf_counter_ns() - start
            cpu1 = resource.getrusage(resource.RUSAGE_SELF)
            candidate = result.messages[2]['content']
            if not isinstance(candidate, str):
                raise RuntimeError('FAIL: unexpected output shape')
            outputs.append(digest(candidate.encode()))
            if trial:
                samples.append({'wall_ns': elapsed, 'cpu_user_seconds': cpu1.ru_utime - cpu0.ru_utime,
                                'cpu_system_seconds': cpu1.ru_stime - cpu0.ru_stime})
        semantic, recovery = recover(raw, candidate, is_json, expand_compacted, is_compacted)
        (args.output / (name + '.headroom.txt')).write_text(candidate)
        original_retrieval_hash = digest(original_path.read_bytes())
        results.append({'fixture': name, 'tokens_raw': len(encoding.encode(raw, disallowed_special=())),
                        'tokens_baseline': len(encoding.encode(baseline, disallowed_special=())),
                        'tokens_headroom': len(encoding.encode(candidate, disallowed_special=())),
                        'utf8_bytes_raw': len(raw.encode()), 'utf8_bytes_headroom': len(candidate.encode()),
                        'baseline_kind': baseline_kind, 'semantic_recovery': semantic, 'roundtrip_recovery': recovery,
                        'baseline_full_fidelity': recover(raw, baseline, is_json, lambda _: None, lambda _: False)[0],
                        'json_recovery_uses_canonical_form': is_json,
                        'original_retrieval_sha256': original_retrieval_hash,
                        'original_unchanged': original_retrieval_hash == before_hash,
                        'deterministic': len(set(outputs)) == 1, 'headroom_lossless_flag': result.lossless,
                        'samples': samples, 'baseline_samples': baseline_samples,
                        'median_hot_wall_ns': statistics.median(x['wall_ns'] for x in samples),
                        'maxrss_kib_process_lifetime': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
    payload = {'state': 'PASS' if all(x['semantic_recovery'] and x['roundtrip_recovery'] and x['original_unchanged'] and x['deterministic'] and x['headroom_lossless_flag'] is True for x in results) else 'FAIL',
               'scope': 'fidelity only; adoption additionally requires documented savings/resource gates',
               'encoding': 'cl100k_base', 'model_label_only_no_inference': 'gpt-4o', 'fixtures': results}
    (args.output / 'metrics.json').write_text(json.dumps(payload, indent=2) + '\n')
    raise SystemExit(0 if payload['state'] == 'PASS' else 1)


if __name__ == '__main__':
    main()

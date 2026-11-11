"""Meaningful negative cases for our verifier. No product/dependency imports."""
import base64
import csv
import hashlib
import io
import json
import unittest
import zipfile
from acquire import eligible, inspect_wheel
from benchmark import typed_equal, recover, cases


def wheel(path='demo/file.py', content=b'x=1\n', corrupt=False):
    metadata = b'Name: demo\nVersion: 1.0\n'
    blobs = {path: content, 'demo-1.0.dist-info/METADATA': metadata}
    rows = []
    for name, data in blobs.items():
        h = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip('=')
        rows.append([name, 'sha256=' + ('broken' if corrupt else h), str(len(data))])
    rows.append(['demo-1.0.dist-info/RECORD', '', ''])
    f = io.StringIO(); csv.writer(f).writerows(rows)
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w') as z:
        for name, data in blobs.items(): z.writestr(name, data)
        z.writestr('demo-1.0.dist-info/RECORD', f.getvalue())
    return out.getvalue()


class OwnedChecks(unittest.TestCase):
    def test_types_not_collapsed(self):
        self.assertFalse(typed_equal(False, 0))
        self.assertFalse(typed_equal({'x': None}, {}))
        self.assertFalse(typed_equal([1, 2], [2, 1]))
    def test_text_loss_detected(self):
        self.assertEqual(recover('NO COMMIT\n', 'COMMIT\n', False, None, None), (False, False))
    def test_json_loss_detected(self):
        self.assertEqual(recover('[{"x":false}]', '[{"x":0}]', True, None, lambda _: False), (False, False))
    def test_json_canonical_recovery(self):
        self.assertEqual(recover('[ { "x": null } ]', '[{"x":null}]', True, None, lambda _: False), (True, True))
    def test_codec_not_original_fallback(self):
        self.assertEqual(recover('[{"x":1}]', 'opaque', True, lambda _: None, lambda _: True), (False, False))
    def test_zip_record(self):
        self.assertTrue(inspect_wheel(wheel(), 'demo', '1.0')['record_verified'])
        with self.assertRaises(ValueError): inspect_wheel(wheel(corrupt=True), 'demo', '1.0')
    def test_zip_traversal(self):
        with self.assertRaises(ValueError): inspect_wheel(wheel('../escape.py'), 'demo', '1.0')
    def test_identity(self):
        with self.assertRaises(ValueError): inspect_wheel(wheel(), 'other', '1.0')
    def test_target_filter(self):
        self.assertTrue(eligible('demo-1.0-cp310-abi3-manylinux_2_28_x86_64.whl'))
        self.assertTrue(eligible('demo-1.0-py3-none-manylinux2014_x86_64.whl'))
        self.assertFalse(eligible('demo-1.0-cp313-cp313-manylinux_2_28_x86_64.whl'))
        self.assertFalse(eligible('demo-1.0-cp312-cp312-musllinux_1_2_x86_64.whl'))
    def test_fixtures_deterministic(self):
        self.assertEqual(list(cases()), list(cases()))
        self.assertEqual(len(list(cases())), 4)


if __name__ == '__main__': unittest.main()

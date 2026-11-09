import csv
import sys
import tempfile
import struct
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / 'tools'))
from paths_to_proxy_timing import convert
from tileplace_vpr import ContractError


class ProxyTimingTests(unittest.TestCase):
    def test_parallel_edges_use_minimum_and_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prefix = root / 'input'
            prefix.with_suffix('.nodes').write_bytes(struct.pack('<IHHIHH', 0, 2, 0, 2, 0, 0))
            prefix.with_suffix('.edges').write_bytes(struct.pack('<IHHIHH', 1, 0, 9, 1, 0, 7))
            prefix.with_suffix('.tasks').write_bytes(struct.pack('<IIIIHHIII', 5, 2, 0, 1, 100, 3, 0, 0, 0))
            paths = root / 'paths.csv'
            paths.write_text('task_id,path_index,resource_id\n5,0,1\n')
            output = root / 'timing.csv'
            self.assertEqual(convert(prefix, paths, output), 1)
            with output.open() as stream:
                self.assertEqual(next(csv.DictReader(stream))['delay_ps'], '7')
            before = output.read_bytes()
            with self.assertRaises(FileExistsError):
                convert(prefix, paths, output)
            self.assertEqual(output.read_bytes(), before)

    def test_invalid_paths_leave_no_partial_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prefix = root / 'input'
            prefix.with_suffix('.nodes').write_bytes(struct.pack('<IHHIHH', 0, 1, 0, 1, 0, 0))
            prefix.with_suffix('.edges').write_bytes(struct.pack('<IHH', 1, 0, 7))
            prefix.with_suffix('.tasks').write_bytes(struct.pack('<IIIIHHIII', 5, 2, 0, 1, 100, 3, 0, 0, 0))
            for body in ['', '5,0,0\n', '5,0,1\n5,0,1\n', '6,0,1\n', '5,0,9\n']:
                paths = root / 'paths.csv'
                paths.write_text('task_id,path_index,resource_id\n' + body)
                output = root / 'timing.csv'
                with self.assertRaises(ContractError):
                    convert(prefix, paths, output)
                self.assertFalse(output.exists())

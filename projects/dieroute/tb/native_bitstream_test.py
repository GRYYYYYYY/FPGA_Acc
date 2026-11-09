"""Strict bit envelope and native completion-report checks, including corrupt inputs."""
from pathlib import Path
import struct
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_native_bitstream import bit_header,drc_counts,route_counts,payload_sha256


def envelope(payload=b'\xff'*16+bytes.fromhex('aa995566')+b'\0'*16):
    data=struct.pack('>H',9)+bytes.fromhex('0ff00ff00ff00ff000')+struct.pack('>H',1)
    for key,value in [(b'a',b'fixture'),(b'b',b'xcu280-fsvh2892-2L-e'),(b'c',b'2026/10/13'),(b'd',b'16:00:00')]:
        data+=key+struct.pack('>H',len(value)+1)+value+b'\0'
    return data+b'e'+struct.pack('>I',len(payload))+payload


class BitstreamTest(unittest.TestCase):
    def test_envelope_and_corruption(self):
        valid=envelope()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'candidate.bit';path.write_bytes(valid)
            value=bit_header(path)
            self.assertEqual(value['part'],'xcu280-fsvh2892-2L-e')
            self.assertEqual(value['payload_bytes'],36)
            self.assertEqual(value['sync_offset_within_payload'],16)
            bad=[b'',valid[:4],valid[:-1],valid+b'\0',valid.replace(b'fixture\0',b'fix\0ure\0',1),
                 b'\0\x08'+valid[2:],valid.replace(b'b\0\x14xcu280',b'a\0\x14xcu280',1),
                 envelope(b'\xff'*36),envelope(b'\xff'+bytes.fromhex('aa995566')+b'\0'*31)]
            # Use the exact located second tag, independent of fixture string length.
            offset=valid.index(b'xcu280')-3;bad[6]=valid[:offset]+b'z'+valid[offset+1:]
            for index,data in enumerate(bad):
                path.write_bytes(data)
                with self.subTest(index=index),self.assertRaises(ValueError):bit_header(path)

    def test_route_completion(self):
        text='\n'.join(f'# of {name}..... : {value} :' for name,value in [('logical nets',12),('routable nets',10),('fully routed nets',10),('nets with routing errors',0)])
        self.assertEqual(route_counts(text)['fully routed nets'],10)
        for bad in [text.replace('fully routed nets..... : 10','fully routed nets..... : 9'),text.replace('routing errors..... : 0','routing errors..... : 1'),text.splitlines()[0]]:
            with self.assertRaises(ValueError):route_counts(bad)

    def test_payload_comparison_ignores_only_header(self):
        with tempfile.TemporaryDirectory() as directory:
            first=Path(directory)/'a.bit';second=Path(directory)/'b.bit'
            raw=envelope();first.write_bytes(raw)
            second.write_bytes(raw.replace(b'16:00:00',b'17:00:00'))
            self.assertNotEqual(first.read_bytes(),second.read_bytes())
            self.assertEqual(payload_sha256(first),payload_sha256(second))
            second.write_bytes(raw[:-1]+b'\1')
            self.assertNotEqual(payload_sha256(first),payload_sha256(second))
            second.write_bytes(raw[:-1])
            with self.assertRaises(ValueError):payload_sha256(second)

    def test_drc_coverage_and_errors(self):
        text='Violations found: 3\n| TEST-1 | Warning | test | 2 |\n| TEST-2 | Advisory | test | 1 |\n'
        self.assertEqual(drc_counts(text)['severities'],{'Warning':2,'Advisory':1})
        for bad in [text.replace('Warning','Error'),text.replace('Warning','Critical Warning'),text.replace('found: 3','found: 4'),text+text.splitlines()[1]+'\n','no report']:
            with self.assertRaises(ValueError):drc_counts(bad)


if __name__=='__main__':unittest.main()

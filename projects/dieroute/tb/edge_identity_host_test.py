"""Exercise host edge identity outputs and fail-closed API boundaries."""
import argparse
import csv
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from native_slr_converter_test import NativeSlrConverterTest, pack


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=Path, required=True)
    args = parser.parse_args()
    host = args.host.resolve()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        def parallel(t):
            t['wires'].extend([[0,'A','source2',0],[1,'A','bridge2',0]])
            t['pips'].append([2,0,1,'A','source2','bridge2','false',0])
        graph = NativeSlrConverterTest().fixture(root, parallel)
        prefix = root/'packed'
        pack(graph, prefix, [(7,0,2)], edge_identity=True)
        # Select the second physical PIP on the identical electrical node pair.
        (root/'packed.edges').write_bytes(struct.pack('<IHHIHHIHH',1,10,0,1,1,0,2,1,0))
        base = {k:v for k,v in os.environ.items() if not k.startswith(('DIEROUTE_','PERSISTROUTE_'))}
        base.update(DIEROUTE_EDGE_IDENTITY='1', DIEROUTE_COST_BITS='64')
        hashes = set()
        for mode in ('flat','hierarchical','downstream','downstream_bounded'):
            for workers in (0,1,2,4):
                output = root/f'run_{mode}_{workers}'
                cmd = [str(host), str(prefix), str(prefix), str(output), mode]
                result = subprocess.run(cmd,env={**base,'DIEROUTE_SPECULATIVE_WORKERS':str(workers)},capture_output=True,text=True)
                assert result.returncode == 0, result.stderr
                paths = list(csv.DictReader(Path(str(output)+'.path_edges.csv').open()))
                trees = list(csv.DictReader(Path(str(output)+'.tree_edges.csv').open()))
                assert [(int(p['edge_id']),int(p['native_pip_key'])) for p in paths] == [(1,4),(2,2)]
                assert [(p['parent'],p['child'],p['edge_id'],p['native_pip_key']) for p in paths] == [(p['parent'],p['child'],p['edge_id'],p['native_pip_key']) for p in trees]
                hashes.add(list(csv.DictReader(Path(str(output)+'.audit.csv').open()))[-1]['route_hash'])
                report=json.loads(Path(str(output)+'.json').read_text())
                assert report['edge_identity'] and report['route_hash_schema']=='task_nodes_and_csr_edges_v1'
        assert len(hashes)==1
        reverse_root=root/'reverse';reverse_root.mkdir()
        def reverse(t):
            p=t['pips'][2]
            p[1],p[2],p[4],p[5],p[6]=p[2],p[1],p[5],p[4],'true'
        graph=NativeSlrConverterTest().fixture(reverse_root,reverse)
        reverse_prefix=reverse_root/'packed'
        pack(graph,reverse_prefix,[(7,0,2)],edge_identity=True)
        for workers in (0,2):
            output=reverse_root/f'run_{workers}'
            result=subprocess.run([str(host),str(reverse_prefix),str(reverse_prefix),str(output),'downstream_bounded'],env={**base,'DIEROUTE_SPECULATIVE_WORKERS':str(workers)},capture_output=True,text=True)
            assert result.returncode==0,result.stderr
            paths=list(csv.DictReader(Path(str(output)+'.path_edges.csv').open()))
            assert [(int(p['edge_id']),int(p['native_pip_key'])) for p in paths]==[(0,0),(1,3)]
        for i,update in enumerate(({'DIEROUTE_COST_BITS':'16'}, {'PERSISTROUTE_TIMING_COMMAND':'false'}, {'DIEROUTE_EDGE_IDENTITY':'0'}, {'DIEROUTE_EDGE_IDENTITY':'2'})):
            output=root/f'rejected_{i}'
            result=subprocess.run([str(host),str(prefix),str(prefix),str(output),'flat'],env={**base,**update},capture_output=True,text=True)
            assert result.returncode==1 and not list(root.glob(output.name+'.*')),result.stderr
        for i,data in enumerate((b'',struct.pack('<3I',0,0,2),struct.pack('<I',0))):
            (root/'packed.edge_ref').write_bytes(data)
            output=root/f'bad_ref_{i}'
            result=subprocess.run([str(host),str(prefix),str(prefix),str(output),'flat'],env=base,capture_output=True,text=True)
            assert result.returncode==1 and not list(root.glob(output.name+'.*')),result.stderr
    print('edge_identity_host PASS: 16 mode/worker runs, 2 reverse-PIP runs, physical keys, hashes, 7 fail-closed cases')


if __name__=='__main__':main()

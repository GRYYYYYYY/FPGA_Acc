"""Host wiring: protected background, terminal ownership and immutable costs."""
import argparse
import csv
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile


def main():
    p=argparse.ArgumentParser();p.add_argument('--host',type=Path,required=True);args=p.parse_args()
    host=str(args.host.resolve())
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);prefix=root/'input'
        def save(suffix,data):Path(str(prefix)+suffix).write_bytes(data)
        save('.nodes',b''.join(struct.pack('<IHH',*x) for x in [(0,2,0),(2,1,0),(3,1,0),(4,0,0)]))
        save('.edges',b''.join(struct.pack('<IHH',*x) for x in [(1,0,0),(2,5,0),(3,0,0),(3,1,0)]))
        resources=[(0,1,256,0,0,0xffffffff),(1,1,9,12,0xffffffff,99),(0,1,256,0,0,0xffffffff),(0,1,256,0,0,0xffffffff)]
        save('.resources',b''.join(struct.pack('<4H2I',*x) for x in resources))
        save('.tasks',struct.pack('<4I2H3I',0,7,0,3,0,8,0,0,0))
        save('.node_die',b'\0'*8);save('.node_box',b'\0'*32)
        save('.node_protection',bytes([0,1,0,0]));save('.edge_protection',b'\0'*4)
        save('.terminal_net',struct.pack('<4I',7,0xffffffff,0xffffffff,7))
        env={k:v for k,v in os.environ.items() if not k.startswith(('DIEROUTE_','PERSISTROUTE_'))}
        env.update(DIEROUTE_EDGE_IDENTITY='1',DIEROUTE_COST_BITS='64',DIEROUTE_MAX_ITERATIONS='3')
        count=0
        for name,update,expected in [('protected_background',None,0),('forbidden_edge',('.edge_protection',bytes([0,0,0,8])),3),('foreign_terminal',('.terminal_net',struct.pack('<4I',7,0xffffffff,8,7)),3)]:
            save('.edge_protection',b'\0'*4);save('.terminal_net',struct.pack('<4I',7,0xffffffff,0xffffffff,7))
            if update:save(*update)
            for mode in ('flat','hierarchical','downstream','downstream_bounded'):
                for workers in (0,1,2,4):
                    output=root/f'{name}_{mode}_{workers}'
                    result=subprocess.run([host,str(prefix),str(prefix),str(output),mode],env={**env,'DIEROUTE_SPECULATIVE_WORKERS':str(workers)},capture_output=True,text=True)
                    assert result.returncode==expected,(name,mode,workers,result.stderr)
                    report=json.loads(Path(str(output)+'.json').read_text());assert report['immutable_admission'] and report['protected_nodes']==1
                    background=struct.unpack_from('<4H2I',Path(str(output)+'.resources').read_bytes(),16)
                    assert background==(1,1,0,0,0xffffffff,99)
                    assert struct.unpack_from('<2Q',Path(str(output)+'.costs').read_bytes(),16)==(9,12)
                    paths=list(csv.DictReader(Path(str(output)+'.paths.csv').open()))
                    assert [int(r['resource_id']) for r in paths]==([2,3] if expected==0 else [])
                    count+=1
        for i,(suffix,data) in enumerate([('.node_protection',b'\0'),('.node_protection',b'\0'*4),('.edge_protection',b'')]):
            save(suffix,data)
            if i==1:Path(str(prefix)+'.terminal_net').unlink()
            output=root/f'bad_{i}'
            result=subprocess.run([host,str(prefix),str(prefix),str(output),'flat'],env=env,capture_output=True,text=True)
            assert result.returncode==1 and not list(root.glob(output.name+'.*'))
    print(f'routing_policy_host PASS: {count} admission/worker/mode runs plus invalid sidecar rejections')


if __name__=='__main__':main()

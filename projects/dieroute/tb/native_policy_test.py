"""Independent byte oracle and rejection cases for native immutable admission."""
import argparse
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
from native_csr_test import FINGERPRINT, crc, table


def container(path, payload):
    header=struct.pack('<8sHHIQQ16sQQ',b'FPGAACCP',0,1,0x44520003,len(payload),len(payload),bytes.fromhex(FINGERPRINT),crc(payload),1)
    path.write_bytes(header+payload)


def main():
    p=argparse.ArgumentParser();p.add_argument('--builder',type=Path,required=True);p.add_argument('--output',type=Path)
    args=p.parse_args()
    if args.output is None:
        scratch=tempfile.TemporaryDirectory();args.output=Path(scratch.name)/'cases'
    out=args.output.resolve();out.mkdir(exist_ok=False,parents=True)
    base=out/'input';base.mkdir()
    for name in ('graph','mapping','footprint','csr'):(base/name).mkdir()
    nodes=[[i,0,i,0,i,m,1,int(i==4),4 if i==5 else 0,0,0,0,0,0,0,0] for i,m in enumerate((1,3,2,1,2,1))]
    pips=[[0,0,1,0,0,1,0,0],[1,2,1,1,2,1,1,2],[2,1,3,0,1,3,0,8],[3,1,4,1,1,4,1,0],[4,3,3,0,3,3,0,4],[5,0xffffffff,0,0,99,0,0,0]]
    table(base/'graph/nodes.bin',nodes);table(base/'graph/pips.bin',pips)
    (base/'graph/intents.csv').write_text('"id","name"\n"0","NODE_LOCAL"\n"1","NODE_GLOBAL_BUFG"\n')
    table(base/'mapping/occupied_nodes.bin',[[3,3,1,1,1,0,0,0]])
    table(base/'mapping/footprint_node_map.bin',[[i] for i in range(6)])
    table(base/'mapping/footprint_pip_map.bin',[[0],[1]])
    table(base/'footprint/nets.bin',[[0]*16,[1]+[0]*15])
    table(base/'footprint/pins.bin',[[0,0,0,1],[0,2,1,0]])
    table(base/'footprint/pips.bin',[[0,0,1,0,0,1,0,0],[0,2,1,1,2,1,1,3]])
    table(base/'footprint/tasks.bin',[[0,0,0,2,0,1,0,1]])
    container(base/'csr/protection.bin',bytes([0,0,0,1,0,8]))
    def patch(path, offset, value):
        data=bytearray(path.read_bytes());struct.pack_into('<I',data,offset,value);path.write_bytes(data)
    def collision(d):
        patch(d/'footprint/nets.bin',64,0)
        with (d/'footprint/pins.bin').open('ab') as f:f.write(struct.pack('<4I',1,0,0,1))
    cases=[('base',lambda d:None,0,None),
        ('forged_background_crc',lambda d:container(d/'csr/protection.bin',bytes([0,0,0,0,0,8])),1,'inherited protection'),
        ('clock_candidate',lambda d:patch(d/'graph/nodes.bin',2*64+7*4,1),3,None),
        ('routethru_candidate',lambda d:patch(d/'graph/pips.bin',32+28,10),3,None),
        ('terminal_collision',collision,1,'terminal node shared'),
        ('wrong_pip_mapping',lambda d:patch(d/'mapping/footprint_pip_map.bin',4,0),1,'endpoint map mismatch'),
        ('wrong_pin_access',lambda d:patch(d/'footprint/pins.bin',16+8,0),1,'pin access SLR'),
        ('unknown_intent',lambda d:patch(d/'graph/nodes.bin',7*4,99),1,'unknown native intent'),
        ('illegal_reverse',lambda d:patch(d/'graph/pips.bin',32+28,0),1,'direction mismatch')]
    records=[]
    for name,mutate,expected,error in cases:
        d=out/name;shutil.copytree(base,d);mutate(d);target=d/'policy'
        cmd=[str(args.builder.resolve()),*[str(d/n) for n in ('graph','mapping','footprint','csr')],FINGERPRINT,str(target)]
        result=subprocess.run(cmd,capture_output=True,text=True);(d/'run.log').write_text(result.stdout+result.stderr)
        assert result.returncode==expected,(name,result.stderr)
        if error:assert error in result.stderr,(name,result.stderr)
        if name=='base':
            payloads={'node_protection.bin':(0x44520004,bytes([0,0,0,1,16,8])),
                      'terminal_net.bin':(0x44520005,struct.pack('<6I',0,0xffffffff,0,0xffffffff,0xffffffff,0xffffffff)),
                      'pip_protection.bin':(0x44520006,bytes([0,0,8,0,4,128]))}
            for filename,(kind,payload) in payloads.items():
                data=(target/filename).read_bytes();assert data[64:]==payload
                assert struct.unpack_from('<I',data,12)[0]==kind and struct.unpack_from('<Q',data,48)[0]==crc(payload)
            a=json.loads((target/'audit.json').read_text())
            assert a['original_candidate_footprint_preserved'] and a['raw_arcs']==6 and a['policy_permitted_arcs_before_net_specific_checks']==3
            assert a['candidate_pins_checked']==a['candidate_pips_checked']==2 and a['cross_slr_tasks']==1
        records.append({'case':name,'exit_code':result.returncode,'passed':True})
    (out/'tests.json').write_text(json.dumps({'passed':True,'cases':records},indent=2)+'\n');print(json.dumps({'passed':True,'cases':len(records)}))


if __name__=='__main__':main()

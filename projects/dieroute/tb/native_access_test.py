"""Noncore components, directed PIP identities, and malformed-input checks."""
import argparse,csv,json,shutil,struct,subprocess,tempfile
from pathlib import Path
from native_csr_test import FINGERPRINT,crc,table

def main():
    p=argparse.ArgumentParser();p.add_argument('--analyzer',type=Path,required=True);p.add_argument('--output',type=Path);args=p.parse_args()
    if args.output is None:
        scratch=tempfile.TemporaryDirectory();args.output=Path(scratch.name)/'cases'
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False);base=out/'input';base.mkdir()
    for name in ('graph','mapping','footprint'):(base/name).mkdir()
    with (base/'graph/tiles.csv').open('w',newline='') as f:
        w=csv.writer(f,quoting=csv.QUOTE_ALL);w.writerow(['address','name','type','slr','column','row','wire_count','pip_begin','pip_count'])
        for i,t in enumerate(('BRAM','INT_INTF_R','INT','CLEL_R')):w.writerow([i,'T'+str(i),t,0,i,0,20,0,0])
    table(base/'graph/nodes.bin',[[i,t,i,t,i,1,1,0,0,0,0,0,0,0,0,0] for i,t in enumerate((0,1,2,2,3,1,3,3))])
    pips=[[i,a,b,0,a,b,0,2 if i==3 else 0] for i,(a,b) in enumerate(((0,1),(1,2),(2,5),(3,5),(3,4),(6,7),(2,3)))]
    table(base/'graph/pips.bin',pips);table(base/'mapping/footprint_node_map.bin',[[i] for i in range(8)])
    order=[0,1,2,3,4,6,5];table(base/'mapping/footprint_pip_map.bin',[[i] for i in order])
    table(base/'footprint/pips.bin',[[int(i==5),*pips[i][1:7],3 if i==3 else 0] for i in order])
    table(base/'footprint/pins.bin',[[0,0,0,1],[0,4,0,0],[1,6,0,1],[1,7,0,0]])
    table(base/'footprint/owners.bin',[[i,int(i>=6)] for i in range(8)])
    table(base/'footprint/nets.bin',[[0,0,0,0,2,0,6,0,1,0,6,1,1,0,0,0],[0,6,2,2,2,6,1,1,1,6,2,1,1,0,0,0]])
    def patch(d,path,offset,value):
        p=d/path;b=bytearray(p.read_bytes());struct.pack_into('<I',b,offset,value);p.write_bytes(b)
    def collision(d):patch(d,'footprint/owners.bin',6*8,0)
    cases=[('base',lambda d:None,None),
        ('missing_tile',lambda d:patch(d,'graph/nodes.bin',12,99),'native node tile identity'),
        ('wrong_pip_map',lambda d:patch(d,'mapping/footprint_pip_map.bin',4,2),'native PIP endpoint identity'),
        ('illegal_reverse',lambda d:patch(d,'graph/pips.bin',3*32+28,0),'native PIP direction'),
        ('duplicate_net_owner',lambda d:patch(d,'footprint/owners.bin',8,0),'net owner identity/order'),
        ('wrong_pin_net',lambda d:patch(d,'footprint/pins.bin',16,1),'pin identity/direction'),
        ('noncore_owner_collision',collision,'noncore node shared')]
    results=[]
    for name,mutate,error in cases:
        d=out/name;shutil.copytree(base,d);mutate(d);target=d/'access'
        cmd=[str(args.analyzer.resolve()),*[str(d/n) for n in ('graph','mapping','footprint')],FINGERPRINT,str(target)]
        r=subprocess.run(cmd,capture_output=True,text=True);(d/'run.log').write_text(r.stdout+r.stderr)
        assert r.returncode==(1 if error else 0),(name,r.stderr)
        if error:assert error in r.stderr,(name,r.stderr)
        else:
            expected={'core_nodes.bin':(0x44520007,bytes([0,0,1,1,0,0,0,0])),
                      'private_owner.bin':(0x44520008,struct.pack('<8I',0,0,0xffffffff,0xffffffff,0,0,1,1)),
                      'access_arcs.bin':(0x44520009,b''.join(struct.pack('<4I',*x) for x in [(0,0,0,1),(0,2,1,2),(0,4,2,5),(0,7,5,3),(0,8,3,4),(1,10,6,7)]))}
            for filename,(kind,payload) in expected.items():
                data=(target/filename).read_bytes();assert data[64:]==payload
                assert struct.unpack_from('<I',data,12)[0]==kind and struct.unpack_from('<Q',data,48)[0]==crc(payload)
            a=json.loads((target/'audit.json').read_text())
            for k,v in {'candidate_nets':2,'candidate_pips':7,'core_core_pips':1,'noncore_incident_pips':6,'candidate_private_noncore_nodes':6,'noncore_components':4,'nonterminal_components':1,'nonterminal_transit_components':1,'source_only_components':1,'sink_only_components':1,'mixed_terminal_components':1,'no_core_boundary_components':1}.items():assert a[k]==v,(k,a[k],v)
        results.append({'case':name,'returncode':r.returncode,'passed':True})
    (out/'tests.json').write_text(json.dumps({'passed':True,'cases':results},indent=2)+'\n');print(json.dumps({'passed':True,'cases':len(results)}))

if __name__=='__main__':main()

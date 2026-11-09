"""Native consumer rejects foreign/background shortcuts and reports cutoffs."""
import argparse,csv,json,shutil,struct,subprocess,tempfile
from pathlib import Path
from native_csr_test import FINGERPRINT,table
from native_search_graph_test import container

def main():
    p=argparse.ArgumentParser();p.add_argument('--probe',type=Path,required=True);p.add_argument('--output',type=Path);a=p.parse_args()
    if a.output is None:scratch=tempfile.TemporaryDirectory();a.output=Path(scratch.name)/'cases'
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);base=out/'input';base.mkdir()
    for name in ('graph','search','footprint','mapping'):(base/name).mkdir()
    table(base/'graph/nodes.bin',[[i,0,i,0,i,3 if i==3 else (2 if i==6 else 1),1,0,0,0,0,0,0,0,0,0] for i in range(8)])
    table(base/'mapping/footprint_node_map.bin',[[i] for i in range(8)])
    tasks=[[0,0,0,6,0,1,0,0],[1,1,4,7,0,0,0,0]];table(base/'footprint/tasks.bin',tasks)
    pairs=[(0,1),(1,2),(1,4),(1,5),(2,3),(3,6),(4,6),(4,7),(5,6)]
    offsets=[0];arcs=[]
    for n in range(8):
        arcs.extend((dst,key*2) for key,(src,dst) in enumerate(pairs) if src==n);offsets.append(len(arcs))
    container(base/'search/offsets.bin',0x44520001,8,struct.pack('<9Q',*offsets))
    container(base/'search/arcs.bin',0x44520002,8,b''.join(struct.pack('<II',*arc) for arc in arcs))
    masks=[0,0,0,0,0,1,0,0];owners=[0,0xffffffff,0xffffffff,0xffffffff,1,0xffffffff,0,1]
    container(base/'search/node_protection.bin',0x4452000a,1,bytes(masks))
    container(base/'search/exclusive_net.bin',0x4452000b,4,struct.pack('<8I',*owners))
    def foreign(d):
        bad=[list(t) for t in tasks];bad[0][2]=4;table(d/'footprint/tasks.bin',bad)
    def blocked(d):
        bad=list(masks);bad[0]=1;container(d/'search/node_protection.bin',0x4452000a,1,bytes(bad))
    def destination(d):
        bad=list(arcs);bad[0]=(8,0);container(d/'search/arcs.bin',0x44520002,8,b''.join(struct.pack('<II',*arc) for arc in bad))
    cases=[('permissions',lambda d:None,100,None),('budget',lambda d:None,2,None),
           ('foreign_seed',foreign,100,'forbidden task endpoint'),('background_seed',blocked,100,'forbidden task endpoint'),
           ('bad_destination',destination,100,'CSR destination bounds')]
    records=[]
    for name,mutate,limit,error in cases:
        d=out/name;shutil.copytree(base,d);mutate(d)
        command=[str(a.probe.resolve()),str(d/'graph'),str(d/'search'),str(d/'footprint'),str(d/'mapping'),FINGERPRINT,str(d/'output'),str(limit),'10','3']
        r=subprocess.run(command,capture_output=True,text=True);(d/'run.log').write_text(r.stdout+r.stderr)
        if error:assert r.returncode==1 and error in r.stderr,(name,r.stderr)
        else:
            assert r.returncode==0,(name,r.stderr)
            report=json.loads((d/'output/audit.json').read_text());rows=list(csv.DictReader((d/'output/paths.csv').open()))
            if name=='permissions':
                assert report['found']==6 and report['budget_exhausted']==0
                for rep in range(3):
                    path=[int(x['destination']) for x in rows if int(x['task'])==0 and int(x['repeat'])==rep]
                    assert path==[1,2,3,6],path
            else:assert report['found']==3 and report['budget_exhausted']==3 and report['exhausted']==0
        records.append(dict(case=name,returncode=r.returncode,passed=True))
    (out/'tests.json').write_text(json.dumps(dict(passed=True,cases=records),indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(records))))
if __name__=='__main__':main()

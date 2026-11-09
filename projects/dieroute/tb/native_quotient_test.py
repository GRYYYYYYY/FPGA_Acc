"""Exact quotient byte oracle, semantic corruption, and guided consumer fixture."""
import argparse,json,shutil,struct,subprocess,tempfile
from pathlib import Path
from native_csr_test import FINGERPRINT,table
from native_search_graph_test import container

def main():
    p=argparse.ArgumentParser()
    for name in ('builder','verifier','probe'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--potential-test',type=Path,required=True)
    p.add_argument('--output',type=Path);a=p.parse_args()
    if a.output is None:scratch=tempfile.TemporaryDirectory();a.output=Path(scratch.name)/'cases'
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    for name in ('graph','search','mapping','footprint'):(out/name).mkdir()
    attributes=[(0,0),(0,0),(1,6),(1,6),(2,19),(3,0),(9,0),(4,0)]
    table(out/'graph/nodes.bin',[[n,t,n,t,n,1,1,intent,0,0,0,0,0,0,0,0] for n,(t,intent) in enumerate(attributes)])
    pairs=[(0,1),(1,2),(1,4),(2,3),(2,7),(3,4),(4,5),(5,7),(7,4)]
    offsets=[0];arcs=[]
    for n in range(8):arcs.extend((b,k*2) for k,(f,b) in enumerate(pairs) if f==n);offsets.append(len(arcs))
    container(out/'search/offsets.bin',0x44520001,8,struct.pack('<9Q',*offsets))
    container(out/'search/arcs.bin',0x44520002,8,b''.join(struct.pack('<II',*e) for e in arcs))
    container(out/'search/node_protection.bin',0x4452000a,1,bytes([0,0,0,0,0,0,1,0]))
    container(out/'search/exclusive_net.bin',0x4452000b,4,struct.pack('<8I',0,*([0xffffffff]*6),0))
    table(out/'mapping/footprint_node_map.bin',[[n] for n in range(8)]);table(out/'footprint/tasks.bin',[[0,0,0,7,0,0,0,0]])
    def run(name,cmd,code=0,error=None):
        r=subprocess.run(list(map(str,cmd)),capture_output=True,text=True);(out/(name+'.log')).write_text(r.stdout+r.stderr)
        assert r.returncode==code,(name,r.stderr)
        if error:assert error in r.stderr,(name,r.stderr)
    run('build',[a.builder.resolve(),out/'graph',out/'search',FINGERPRINT,out/'quotient'])
    expected={'node_groups.bin':(0x4452000d,4,struct.pack('<8I',0,0,1,1,2,3,0xffffffff,4)),
              'reverse_offsets.bin':(0x4452000e,8,struct.pack('<6Q',0,0,1,4,5,7)),
              'reverse_sources.bin':(0x4452000f,4,struct.pack('<7I',0,0,1,4,2,1,3)),
              'groups.bin':(0x44520010,8,b''.join(struct.pack('<II',*x) for x in [(0,0),(1,6),(2,19),(3,0),(4,0)]))}
    for name,(kind,width,payload) in expected.items():
        oracle=out/('expected_'+name);container(oracle,kind,width,payload);assert (out/'quotient'/name).read_bytes()==oracle.read_bytes(),name
    def verify(name,q,error=None):run(name,[a.verifier.resolve(),out/'graph',out/'search',q,FINGERPRINT,out/(name+'_out')],1 if error else 0,error)
    verify('verify',out/'quotient')
    run('potential',[a.potential_test.resolve(),out/'quotient',FINGERPRINT])
    def mutate(name,changes,error):
        q=out/name;shutil.copytree(out/'quotient',q)
        for file,payload in changes.items():kind,width,_=expected[file];container(q/file,kind,width,payload)
        verify(name,q,error)
    mutate('missing_edge',{'reverse_offsets.bin':struct.pack('<6Q',0,0,0,3,4,6),'reverse_sources.bin':struct.pack('<6I',0,1,4,2,1,3)},'native edge missing')
    mutate('extra_edge',{'reverse_offsets.bin':struct.pack('<6Q',0,1,2,5,6,8),'reverse_sources.bin':struct.pack('<8I',4,0,0,1,4,2,1,3)},'invented quotient edge')
    mutate('wrong_group',{'node_groups.bin':struct.pack('<8I',1,0,1,1,2,3,0xffffffff,4)},'descriptor mismatch')
    mutate('protected_group',{'node_groups.bin':struct.pack('<8I',0,0,1,1,2,3,0,4)},'protected node has group')
    mutate('duplicate_group',{'groups.bin':expected['groups.bin'][2][:-8]+struct.pack('<II',0,0)},'duplicate group descriptor')
    run('guided',[a.probe.resolve(),out/'graph',out/'search',out/'footprint',out/'mapping',FINGERPRINT,out/'probe','100','2','5',out/'quotient'])
    import csv
    rows=list(csv.DictReader((out/'probe/results.csv').open()));assert len(rows)==5
    assert all(r['status']=='found' and int(r['hops'])==3 and int(r['lower_bound'])==2 for r in rows)
    run('radius',[a.probe.resolve(),out/'graph',out/'search',out/'footprint',out/'mapping',FINGERPRINT,out/'radius_probe','100','2','5',out/'quotient','source_radius'])
    bounded=list(csv.DictReader((out/'radius_probe/results.csv').open()))
    assert all(r['status']=='found' and int(r['hops'])==3 and int(r['lower_bound'])==2 for r in bounded)
    assert all(int(b['quotient_edge_visits'])<=int(r['quotient_edge_visits']) for r,b in zip(rows,bounded))
    (out/'tests.json').write_text(json.dumps({'passed':True,'cases':10})+'\n');print('10 quotient/consumer cases passed')
if __name__=='__main__':main()

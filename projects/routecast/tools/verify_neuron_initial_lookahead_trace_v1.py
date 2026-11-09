"""Reconstruct every observed initialized SOURCE map candidate and native minimum."""
import json,math,struct,sys,hashlib
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def f(x):return struct.unpack('<f',int(x,16).to_bytes(4,'little'))[0]
def bits(x):return struct.pack('<f',x).hex()
def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]
def main(root):
 root=Path(root);work=root/'work';prior=R/'experiments/neuron_initial_lookahead_snapshot_v1_2026-10-17'
 assert json.loads((root/'lookahead_verification.json').read_text())['all_pass']
 for n in ['criticality.tsv','timing.tsv','lookahead_delay.tsv']:assert sha(work/n)==sha(prior/'work'/n)
 manifest=json.loads((R/'experiments/titan23_neuron_native_inputs_v1_2026-10-13/criticality/initial_connection_criticalities.json').read_text());pins={(x['net'],x['local_sink_pin']):x for x in manifest}
 expected=[]
 for line in (work/'lookahead_delay.tsv').open():
  p=line.strip().split('\t');m=pins[(int(p[2]),int(p[4]))];expected.append((m['source_rr'],m['target_rr'],p[6]))
 counts=Counter();query=0;active=None;maps=[];examples=[]
 with (work/'lookahead_trace.tsv').open() as stream:
  for line in stream:
   p=line.strip().split('\t');kind=p[0]
   if kind=='Q':
    assert active is None and not maps;query+=1;assert int(p[1])==query and tuple(map(int,p[2:4]))==expected[query-1][:2]
   elif kind=='M':
    assert active is None and int(p[1])==query
    active=dict(id=int(p[2]),count=int(p[6]),entries=[],wires=[])
   elif kind=='E':
    assert int(p[1])==query and int(p[2])==active['id'];active['entries'].append((int(p[3]),int(p[4]),int(p[5]),int(p[6]),f(p[7]),f(p[8])))
   elif kind=='W':
    assert int(p[1])==query and int(p[2])==active['id'];active['wires'].append((int(p[3]),int(p[4]),int(p[5]),f(p[6]),f(p[7])))
   elif kind=='R':
    assert int(p[1])==query and int(p[2])==active['id'] and len(active['entries'])==active['count']
    assert active['entries'],'Empty maps require separate huge-value handling; do not silently skip'
    w=iter(active['wires']);candidates=[]
    for key,typ,seg,layer,delay,cong in active['entries']:
     if typ==1:wd=wc=0.0
     else:
      t,s,l,wd,wc=next(w);assert (t,s,l)==(typ,seg,layer)
     candidates.append((f32(delay+wd),f32(cong+wc),typ,key))
    assert next(w,None) is None
    assert bits(min(x[0] for x in candidates))==bits(f(p[3])) and bits(min(x[1] for x in candidates))==bits(f(p[4]))
    maps.append((f(p[3]),any(x[0]==0 and x[2]==1 for x in candidates),any(x[0]==0 and x[2]!=1 for x in candidates)))
    counts['map_calls']+=1;counts['entries']+=len(candidates);counts['wire_callbacks']+=len(active['wires']);active=None
   elif kind=='Z':
    assert active is None and int(p[1])==query and maps
    value=f(p[2]);assert bits(value)==bits(f(expected[query-1][2]))==bits(min(x[0] for x in maps))
    counts['queries']+=1;counts['zero_queries']+=value==0
    counts['zero_with_sink_candidate']+=value==0 and any(x[1] for x in maps)
    counts['zero_with_non_sink_candidate']+=value==0 and any(x[2] for x in maps)
    if value==0 and len(examples)<8:examples.append(dict(query=query,source=expected[query-1][0],sink=expected[query-1][1],map_minima=maps))
    maps=[]
   else:raise AssertionError(kind)
 assert query==counts['queries']==77106 and active is None and not maps and counts['zero_queries']==76968
 out=dict(all_pass=True,counts=dict(counts),examples=examples,prior_three_output_files_byte_identical=True,all_native_map_minima_and_query_delays_reconstructed=True,bindings={str(p):sha(p) for p in [Path(__file__).resolve(),root/'lookahead_verification.json',work/'lookahead_trace.tsv',work/'lookahead_delay.tsv']},scope='Exact observed candidate accounting, no native source or budget change; zero candidate does not establish physical zero route delay.',promoted=False)
 (root/'trace_verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out['counts'],indent=2))
if __name__=='__main__':main(sys.argv[1])

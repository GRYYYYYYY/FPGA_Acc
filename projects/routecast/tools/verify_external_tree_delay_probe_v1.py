"""Independent zero-RC physical switch recurrence versus actual native tree delays."""
import sys,json,struct,hashlib,xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from native_route_ledger_import_compact import physical_paths
from zero_rc_budget_certificate_graph_v1 import load_graph
D=R/'experiments/prospective_external_family_tree_delay_probe_v1_2026-10-19'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def f32(v):return struct.unpack('f',struct.pack('f',v))[0]
def bits(v):return struct.pack('f',v).hex()
def main():
 protocol=json.loads((D/'protocol.json').read_text());terminal=json.loads((D/'terminal.json').read_text())
 assert all(sha(p)==h for p,h in terminal['bindings'].items())
 graph=R/'experiments/prospective_external_family_width_frame_inputs_v1_2026-10-19/w160/source/rr_graph.xml'
 g=load_graph(graph);switch={}
 for _,e in ET.iterparse(graph,events=('end',)):
  if e.tag=='switch' and e.find('timing') is not None:
   switch[int(e.get('id'))]=f32(float(e.find('timing').get('Tdel','0')))
  if e.tag in ('node','edge'):e.clear()
 assert set(switch)==set(g['weights'])
 assert all(bits(v)==bits(g['weights'][k]/1e18) for k,v in switch.items())
 arcs={(u,v,s) for u,v,s in zip(g['us'],g['vs'],g['switches'])};rows=[];bindings={str(graph):sha(graph),str(Path(__file__).resolve()):sha(__file__),str(D/'protocol.json'):sha(D/'protocol.json'),str(D/'terminal.json'):sha(D/'terminal.json')}
 for c,t in zip(protocol['cases'],terminal['rows']):
  assert c['case']==t['case'] and t['exit_status']==0 and t['import_probe_marker_present'] and not t['router_search_completed']
  out=Path(c['directory']);p=out/'native_import.tsv';bindings[str(p)]=sha(p);bindings[c['seed']]=sha(c['seed']);names={};sinks={};values={};sources={}
  for line in p.read_text().splitlines():
   x=line.split('\t')
   if x[0]=='NAME':names[int(x[1])]=x[2]
   elif x[0]=='T' and x[3]=='1':sources[int(x[1])]=int(x[4])
   elif x[0]=='P':sinks[int(x[1]),int(x[2])]=int(x[3])
   elif x[0]=='D':values[int(x[1]),int(x[2])]=f32(float(x[3]))
  assert set(sinks)==set(values) and len(values)==15616
  paths=physical_paths(c['seed']);lookup={}
  for name,pp in paths.items():
   for path in pp:
    key=(name,path[0][0],path[-1][0]);assert key not in lookup or lookup[key]==path;lookup[key]=path
  mismatch=[];single=[];edges=0
  for (net,pin),actual in values.items():
   path=lookup[names[net],sources[net],sinks[net,pin]];delay=f32(0);integer=0
   for (u,_),(v,s) in zip(path,path[1:]):
    assert (u,v,s) in arcs;delay=f32(delay+switch[s]);integer+=g['weights'][s];edges+=1
   if bits(delay)!=bits(actual):mismatch.append(dict(net=net,pin=pin,native=actual,recurrence=delay))
   once=f32(integer/1e18)
   if bits(once)!=bits(actual):single.append(dict(net=net,pin=pin,native=actual,once=once))
  (out/'arithmetic_mismatches.json').write_text(json.dumps(dict(recurrence=mismatch,single_cast=single),indent=2)+'\n')
  rows.append(dict(case=c['case'],connections=len(values),physical_arc_visits=edges,recurrence_mismatches=len(mismatch),single_cast_mismatches=len(single)))
  print(rows[-1],flush=True)
 result=dict(status='ALL3_NATIVE_TREE_FLOAT32_RECURRENCE_EXACT' if all(r['recurrence_mismatches']==0 for r in rows) else 'RECURRENCE_FAILED',rows=rows,bindings=bindings,scope='Certified zero-RC graph only, actual native import; no changed-pin local timing invariance or forecast quality claim.')
 (D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');assert all(r['recurrence_mismatches']==0 for r in rows)
if __name__=='__main__':main()

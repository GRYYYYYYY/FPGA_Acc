"""Independent XML/Fraction floor and native-path proof plus full printed audit."""
import json,hashlib,xml.etree.ElementTree as ET
from fractions import Fraction as F
from pathlib import Path
from collections import defaultdict,Counter
from unified_rr_audit_inventory_v1 import read
from stream_native_route_audit_unified_v1 import audit
R=Path(__file__).resolve().parents[1];D=R/'experiments/xtea_native_state_bootstrap_v1_2026-10-18'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
r=json.loads((D/'receipt.json').read_text());assert all(sha(p)==h for p,h in r['bindings'].items());frame=json.loads((D/'initial.json').read_text());protocol=json.loads((R/'experiments/native_state_bootstrap_protocol_v1_2026-10-18/protocol.json').read_text());meta=json.loads(Path(protocol['previous_endpoint']).read_text());graph=Path(meta['inputs']['graph']['path']);xml=ET.parse(graph).getroot();nodes={int(n.get('id')):n for n in xml.find('rr_nodes')};edges=[tuple(int(e.get(k)) for k in ['src_node','sink_node','switch_id']) for e in xml.find('rr_edges')];switches={int(s.get('id')):s for s in xml.find('switches')};scale=frame['scale'];assert scale%10**9==0
initial={};rc={};sw={}
for nid,n in nodes.items():
 t=n.find('timing');rr=F(t.get('R'));cc=F(t.get('C'));assert rr>=0 and cc>=0;rc[nid]=(rr,cc);initial[nid]=rr*cc/2
for sid,s in switches.items():
 assert s.get('type') in {'buffer','mux','tristate'};t=s.find('timing');assert F(t.get('Cinternal','0'))==0;sw[sid]=(F(t.get('R','0')),F(t.get('Tdel','0')))
weights=[];adj=defaultdict(list);cache={}
for eid,(u,v,s) in enumerate(edges):
 key=(rc[v],sw[s])
 if key not in cache:
  (rr,cc),(sr,td)=key;value=((sr+rr/2)*cc+td)*scale;assert value.denominator==1 and value>=0;cache[key]=value.numerator
 weights.append(cache[key]);adj[u].append((v,cache[key]))
by_source=defaultdict(list)
for rec in frame['records']:by_source[rec['source']].append(rec)
assert len(frame['records'])==len(meta['connections'])==2450
qs={q['connection_id']:q for q in meta['connections']};assert set(qs)=={r['connection_id'] for r in frame['records']};checks=0;certsources=set();nativepaths=json.loads((D/'native_paths.json').read_text());unions=defaultdict(set)
for spec in r['certificates']:
 assert sha(spec['path'])==spec['sha256'];c=json.loads(Path(spec['path']).read_text());source=c['source'];assert source not in certsources;certsources.add(source);clip=c['clip'];pot={int(n):v for n,v in c['potentials'].items()};assert all(n in nodes and int(nodes[n].get('capacity'))>0 and 0<=v<clip for n,v in pot.items());assert F(pot.get(source,clip),scale)<=initial[source]
 # All default-clip source edges satisfy inequality by nonnegative weights.
 for u,value in pot.items():
  for v,w in adj[u]:
   if int(nodes[v].get('capacity'))>0:assert pot.get(v,clip)<=value+w;checks+=1
 def path_value(source,target,ids):
  node=source;value=initial[source];seen={source};path=[(source,None)]
  for eid in ids:
   u,v,s=edges[eid];assert u==node and v not in seen and int(nodes[v].get('capacity'))>0;seen.add(v);value+=F(weights[eid],scale);node=v;path.append((v,s))
  assert node==target;return value,path
 assert {int(t) for t in c['witnesses']}=={q['sink'] for q in by_source[source]}
 for rec in by_source[source]:
  cid=rec['connection_id'];assert all(rec[k]==v for k,v in qs[cid].items());target=rec['sink'];floor,_=path_value(source,target,c['witnesses'][str(target)]);assert floor==F(pot.get(target,clip),scale)==F(rec['floor_integer'],scale)
  value,path=path_value(source,target,rec['answer']['physical_edge_ids']);assert value==F(rec['answer']['delay'],scale);assert [list(x) for x in path]==nativepaths[str(cid)];assert floor<=value;budget=max(F(1,10**9),F((3*rec['floor_integer']+1)//2,scale),value);assert budget==F(rec['budget_integer'],scale);unions[rec['net_id']].update(n for n,s in path)
assert certsources==set(by_source)
inv=read(graph,meta['graph_sha256']);physical=audit(graph,protocol['previous_native_route'],inv);occupancy=Counter(n for used in unions.values() for n in used);assert {str(n):v for n,v in occupancy.items()}==frame['ledger']==physical['node_occupancy'];assert physical['overflow_units']==0;assert not frame['history'];assert all(v==0 for v in frame['epochs'].values());assert all(sha(p)==h for p,h in r['bindings'].items())
with (D/'independent_xml_verification_v1.json').open('x') as f:json.dump(dict(bindings={**r['bindings'],str(D/'receipt.json'):sha(D/'receipt.json'),str(Path(__file__)):sha(__file__)},connections=2450,nets=len(unions),source_certificates=len(certsources),nontrivial_potential_edge_checks=checks,default_clip_edges_proven_by_nonnegative_weights=True,all_native_paths_exact=True,all_raw_floors_certified=True,all_native_delays_and_budgets_exact=True,all_uniqueNET_occupancy_matches_full_printed_audit=True,canonical_gate='Separate archived ignored-pin semantic evidence; original zero-counter false',scope='Original native-state bootstrap correctness, not target update, native STA guarantee, heldout or gain.'),f,indent=2);f.write('\n')
print('PASS independent XML native bootstrap',2450,'connections',len(certsources),'floor certificates',flush=True)

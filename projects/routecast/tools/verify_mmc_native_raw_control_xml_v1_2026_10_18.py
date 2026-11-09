"""Independent streamed XML/Fraction floor, complete paths and NET ledger proof."""
import json,time,xml.etree.ElementTree as ET
from pathlib import Path
from array import array
from fractions import Fraction as F
from collections import defaultdict,Counter
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_native_raw_control_v1_2026-10-18';start=time.perf_counter();rp=D/'receipt.json';r=json.loads(rp.read_text());assert all(sha(p)==h for p,h in r['bindings'].items());frame=json.loads((D/'initial.json').read_text());scale=frame['scale'];assert type(scale) is int and scale>0 and scale%10**9==0;G=R/'experiments/mmc_native_state_geometry_v1_2026-10-18';g=json.loads((G/'protocol.json').read_text());old=json.loads(Path(g['previous_endpoint']).read_text());P=R/'experiments/mmc_native_state_swap_inputs_v1_2026-10-18';meta=json.loads((P/'demand/endpoints.json').read_text());proof=json.loads((P/'staged_input_verification_v1.json').read_text());assert all(sha(p)==h for p,h in proof['bindings'].items());dirty=set(proof['affected']['affected_net_ids']);assert sorted(dirty)==r['dirty_nets'];graph=Path(meta['inputs']['graph']['path']);assert sha(graph)==old['graph_sha256']==meta['graph_sha256'];caps=array('I');types=[];nodeclasses=array('I');classes=[];lookup={};switches={};us=array('I');vs=array('I');ss=array('I');weights=array('Q');cost_cache={};stack=[]
print('MMC INDEPENDENT XML READ START',flush=True)
for event,e in ET.iterparse(graph,events=('start','end')):
 if event=='start':stack.append(e);continue
 parent=stack[-2].tag if len(stack)>1 else None
 if e.tag=='node' and parent=='rr_nodes':
  assert int(e.get('id'))==len(caps);caps.append(int(e.get('capacity')));types.append(e.get('type'));t=e.find('timing');key=(t.get('R'),t.get('C'))
  if key not in lookup:
   rr,cc=map(F,key);assert rr>=0 and cc>=0;lookup[key]=len(classes);classes.append((rr,cc))
  nodeclasses.append(lookup[key])
 elif e.tag=='switch' and parent=='switches':
  sid=int(e.get('id'));assert sid not in switches and e.get('type') in {'buffer','mux','tristate'};t=e.find('timing');assert F(t.get('Cinternal','0'))==0;sr,td=F(t.get('R','0')),F(t.get('Tdel','0'));assert sr>=0 and td>=0;switches[sid]=(sr,td)
 elif e.tag=='edge' and parent=='rr_edges':
  u,v,s=(int(e.get(k)) for k in ['src_node','sink_node','switch_id']);assert not us or u>=us[-1];assert u<len(caps) and v<len(caps);us.append(u);vs.append(v);ss.append(s);key=nodeclasses[v],s
  if key not in cost_cache:
   rr,cc=classes[key[0]];sr,td=switches[s];value=((sr+rr/2)*cc+td)*scale;assert value.denominator==1 and 0<=value<2**64;cost_cache[key]=value.numerator
  weights.append(cost_cache[key])
 if (e.tag,parent) in [('node','rr_nodes'),('switch','switches'),('edge','rr_edges')]:stack[-2].remove(e);e.clear()
 stack.pop()
initial=[]
for rr,cc in classes:
 value=rr*cc/2*scale;assert value.denominator==1;initial.append(value.numerator)
offsets=array('Q',[0])*(len(caps)+1)
for u in us:offsets[u+1]+=1
for n in range(len(caps)):offsets[n+1]+=offsets[n]
oldpaths={}
for name,paths in physical_paths(g['previous_native_route']).items():
 for path in paths:
  key=name,path[0][0],path[-1][0];assert key not in oldpaths;oldpaths[key]=path
queries={q['connection_id']:q for q in meta['connections']};before={q['connection_id']:q for q in old['connections']};assert queries.keys()==before.keys();records={x['connection_id']:x for x in frame['records']};assert len(records)==len(frame['records'])==len(queries)==frame['required_connections']==frame['completed_connections']==115572;owners=defaultdict(set);parents=defaultdict(dict);by_source=defaultdict(list);unknown=0
for cid,q in queries.items():
 rec=records[cid];assert all(rec[k]==v for k,v in q.items());u=q['source'];assert types[u]=='SOURCE' and caps[u]>0;value=initial[nodeclasses[u]];seen={u};path=[(u,None)]
 for eid in rec['answer']['physical_edge_ids']:
  assert type(eid) is int and 0<=eid<len(us) and us[eid]==u;v=vs[eid];assert v not in seen and caps[v]>0;seen.add(v);value+=weights[eid];path.append((v,ss[eid]))
  if types[v]!='SINK':
   assert types[v]!='SOURCE';edge=(u,eid);net=q['net_id'];assert v not in parents[net] or parents[net][v]==edge;parents[net][v]=edge
  u=v
 assert u==q['sink'] and types[u]=='SINK' and value==rec['answer']['delay']<=rec['budget_integer'];owners[q['net_id']].update(seen)
 if q['net_id'] in dirty:
  assert rec['floor_integer']==value and rec['budget_integer']==max(scale//10**9,(3*value+1)//2);by_source[q['source']].append(rec)
 else:
  assert q==before[cid];assert path==oldpaths[meta['net_names'][str(q['net_id'])],q['source'],q['sink']];assert rec['floor_integer'] is None;unknown+=1;assert rec['budget_integer']==max(scale//10**9,value)
assert unknown==r['preserved_connections']==115092 and sum(map(len,by_source.values()))==480
print('MMC ALL115572 PATHS/RC/BUDGETS PASS',flush=True)
seen_sources=set();inequalities=0
for spec in r['certificates']:
 assert sha(spec['path'])==spec['sha256'];c=json.loads(Path(spec['path']).read_text());source=c['source'];assert source not in seen_sources and source in by_source;seen_sources.add(source);clip=c['clip'];pot={int(n):v for n,v in c['potentials'].items()};assert caps[source]>0 and pot.get(source,clip)<=initial[nodeclasses[source]];assert all(0<=n<len(caps) and caps[n]>0 and type(v) is int and 0<=v<clip for n,v in pot.items())
 # All source-default-clip edges hold by globally verified nonnegative weights.
 for u,value in pot.items():
  for slot in range(offsets[u],offsets[u+1]):
   v=vs[slot]
   if caps[v]>0:assert pot.get(v,clip)<=value+weights[slot];inequalities+=1
 assert {int(t) for t in c['witnesses']}=={q['sink'] for q in by_source[source]}
 for rec in by_source[source]:assert rec['answer']['physical_edge_ids']==c['witnesses'][str(rec['sink'])] and rec['floor_integer']==pot.get(rec['sink'],clip)
assert seen_sources==set(by_source)
ledger=Counter(n for used in owners.values() for n in used);overflow=sum(max(0,v-caps[n]) for n,v in ledger.items());assert frame['ledger']=={str(n):v for n,v in ledger.items()};assert overflow==frame['overflow_units']==r['overflow_units'];assert not frame['eligible_for_legal_route_commit']
bindings={**r['bindings'],str(rp):sha(rp),str(Path(__file__)):sha(__file__)};bindings.update({c['path']:c['sha256'] for c in r['certificates']});assert all(sha(p)==h for p,h in bindings.items())
with (D/'independent_xml_verification_v1.json').open('x') as f:json.dump(dict(bindings=bindings,connections=115572,certified_dirty_floors=480,source_certificates=len(seen_sources),preserved_native_paths=unknown,nontrivial_potential_inequalities=inequalities,all_other_default_clip_edges_proven_by_nonnegative_weights=True,all_paths_original_XML_fraction_RC_budget_singleparent_and_uniqueNET_pass=True,all_unchanged_native_paths_exact=True,old_floors_explicitly_unknown_not_falsely_certified=True,overflow_units=overflow,verification_seconds=time.perf_counter()-start,scope='Independent exact XML/Fraction extraction and full raw-control frame proof. Congested prediction not native route; no source criticality/full-old-floor or local feedback admission, canonical target routing or timing gain.'),f,indent=2);f.write('\n')
print('PASS MMC RAW INDEPENDENT XML',overflow,'overflow',len(seen_sources),'certificates',flush=True)

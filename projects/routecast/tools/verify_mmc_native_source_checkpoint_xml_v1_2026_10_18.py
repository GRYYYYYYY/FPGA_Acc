"""Independent original XML/Fraction all-native MMC source checkpoint audit."""
import json,time,xml.etree.ElementTree as ET
from pathlib import Path
from array import array
from fractions import Fraction as F
from collections import defaultdict,Counter
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18';start=time.perf_counter();rp=D/'receipt.json';receipt=json.loads(rp.read_text());assert all(sha(p)==h for p,h in receipt['bindings'].items());frame=json.loads((D/'initial.json').read_text());scale=frame['scale'];assert scale==10**18
ready_path=R/'experiments/mmc_native_state_geometry_v1_2026-10-18/readiness_verification_v1.json';ready=json.loads(ready_path.read_text());assert ready['native_canonical_semantic_pass'] and not ready['original_zero_counter_gate'] and ready['ignored_pin_fixups']==330;assert all(sha(p)==h for p,h in ready['bindings'].items())
gp=R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json';g=json.loads(gp.read_text());ep=Path(g['previous_endpoint']);meta=json.loads(ep.read_text());graph=Path(meta['inputs']['graph']['path']);assert sha(graph)==meta['graph_sha256']
caps=array('I');types=[];nodeclasses=array('I');classes=[];lookup={};switches={};us=array('I');vs=array('I');ss=array('I');weights=array('Q');cost_cache={};stack=[]
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

observed={}
for name,branches in physical_paths(g['previous_native_route']).items():
 for path in branches:
  key=name,path[0][0],path[-1][0];assert key not in observed;observed[key]=tuple(path)
queries={q['connection_id']:q for q in meta['connections']};records={r['connection_id']:r for r in frame['records']};assert len(records)==len(frame['records'])==len(queries)==115572
fp=R/'experiments/mmc_retained_tree_full_schedule_recovery_v1_2026-10-13/model/floors.json';assert receipt['bindings'][str(fp)]==sha(fp);floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads(fp.read_text())}
owners=defaultdict(set);parents=defaultdict(dict);independent=Counter();anchors=0;expectedkeys=set()
for cid,q in queries.items():
 record=records[cid];assert all(record[k]==v for k,v in q.items());u=q['source'];assert types[u]=='SOURCE' and caps[u]>0;delay=initial[nodeclasses[u]];seen={u};path=[(u,None)]
 for eid in record['answer']['physical_edge_ids']:
  assert type(eid) is int and 0<=eid<len(us) and us[eid]==u;v=vs[eid];assert v not in seen and caps[v]>0;seen.add(v);delay+=weights[eid];path.append((v,ss[eid]))
  if types[v]!='SINK':
   assert types[v]!='SOURCE';edge=(u,eid);net=q['net_id'];assert v not in parents[net] or parents[net][v]==edge;parents[net][v]=edge
  u=v
 assert u==q['sink'] and types[u]=='SINK' and delay==record['answer']['delay']
 key=meta['net_names'][str(q['net_id'])],q['source'],q['sink'];assert key not in expectedkeys;expectedkeys.add(key);assert tuple(path)==observed[key]
 floor=floors[q['source'],q['sink']];assert type(floor) is int and 0<=floor<=delay and floor==record['floor_integer']
 proxy=max(scale//10**9,(3*floor+1)//2);assert record['proxy_budget_integer']==proxy and record['budget_integer']==max(proxy,delay);anchors+=delay>proxy
 owners[q['net_id']].update(seen);independent.update(seen)
assert expectedkeys==set(observed)
ledger=Counter(n for ns in owners.values() for n in ns);assert frame['ledger']=={str(n):v for n,v in ledger.items()};assert frame['independent_connection_ledger']=={str(n):v for n,v in independent.items()}
assert all(v<=caps[n] for n,v in ledger.items()) and frame['overflow_units']==0 and frame['history']=={} and frame['epochs']=={str(net):0 for net in owners}
assert frame['completed_connections']==frame['required_connections']==len(records)
bindings={**receipt['bindings'],**ready['bindings'],str(ready_path):sha(ready_path),str(rp):sha(rp),str(Path(__file__)):sha(__file__)};assert all(sha(p)==h for p,h in bindings.items())
result=dict(bindings=bindings,connections=len(records),nets=len(owners),all_native_paths_exact=True,all_native_delays_and_budgets_exact=True,all_uniqueNET_occupancy_matches_full_printed_audit=True,all_paths_original_XML_fraction_RC_budget_singleparent_and_uniqueNET_pass=True,independent_connection_ledger_exact=True,anchored_above_proxy=anchors,all_old_per_design_minima_independently_recertified=False,all_raw_floors_certified=False,archived_native_canonical_semantic_pass=True,original_zero_counter_gate=False,ignored_pin_fixups=330,verification_seconds=time.perf_counter()-start,scope='All actual native source paths and additive RC/budgets, physical parent/capacity/ledgers independently checked against original XML and original printed physical paths. Existing source route canonical semantic acceptance remains archived. Cached F provenance retained; no new global floor minimum dual certificate, real STA guarantee, target native run or end-to-end gain.')
with (D/'independent_xml_verification_v1.json').open('x') as o:json.dump(result,o,indent=2)
print('MMC SOURCE XML/FRACTION PASS',len(records),'connections','anchors',anchors,'seconds',result['verification_seconds'],flush=True)

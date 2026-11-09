"""Independent XML/Fraction matched-V2 initializer path/budget/retention audit."""
import json,sys,time,xml.etree.ElementTree as ET
from pathlib import Path
from array import array
from fractions import Fraction as F
from collections import Counter,defaultdict
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=Path(sys.argv[2]);tick=time.perf_counter();rp=D/'receipt.json';receipt=json.loads(rp.read_text());assert all(sha(p)==h for p,h in receipt['bindings'].items());bindings={**receipt['bindings'],str(rp):sha(rp),str(Path(__file__)):sha(__file__)}
source=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18';old={x['connection_id']:x for x in json.loads((source/'initial.json').read_text())['records']};ep=Path(sys.argv[1])/'demand/endpoints.json';meta=json.loads(ep.read_text());queries={q['connection_id']:q for q in meta['connections']};graph=Path(meta['inputs']['graph']['path']);assert sha(graph)==meta['graph_sha256'];scale=10**18
rawref=D/'fresh_raw';ip=rawref/'independent_xml_verification_v2.json';independent=json.loads(ip.read_text());assert independent['all_paths_original_XML_fraction_RC_budget_singleparent_and_uniqueNET_pass'];assert all(sha(p)==h for p,h in independent['bindings'].items());bindings.update(independent['bindings']);bindings[str(ip)]=sha(ip);fresh=json.loads((rawref/'receipt.json').read_text());minimum={x['connection_id']:x for x in json.loads((rawref/'initial.json').read_text())['records']}
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

direct={cid for cid,q in queries.items() if (q['source'],q['sink'])!=(old[cid]['source'],old[cid]['sink'])};dirty={queries[cid]['net_id'] for cid in direct};closure={cid for cid,q in queries.items() if q['net_id'] in dirty};staged=json.loads((Path(sys.argv[1])/'staged_input_verification_v1.json').read_text());assert direct==set(staged['affected']['changed_connection_ids']) and dirty==set(staged['affected']['affected_net_ids']) and closure==set(staged['affected']['recompute_connection_ids'])
expected={};expected_f={}
for cid,q in queries.items():
 floor=minimum[cid]['floor_integer'] if cid in direct else old[cid]['floor_integer'];expected_f[cid]=floor;proxy=max(scale//10**9,(3*floor+1)//2);expected[cid]=proxy if cid in direct else max(proxy,old[cid]['answer']['delay'])
 if cid in closure-direct:assert minimum[cid]['floor_integer']==floor
rows=[];allrecords={}
for mode in ['raw_min','native_retained']:
 frame=json.loads((D/mode/'initial.json').read_text());records={r['connection_id']:r for r in frame['records']};allrecords[mode]=records;assert len(records)==len(frame['records'])==len(queries)==115572;assert frame['scale']==scale and frame['budget_policy']=='NATIVE_ENDPOINT_ANCHORED_PROXY_V2'
 owners=defaultdict(set);parents=defaultdict(dict);independent_ledger=Counter()
 for cid,q in queries.items():
  r=records[cid];assert all(r[k]==v for k,v in q.items());assert r['floor_integer']==expected_f[cid] and r['budget_integer']==expected[cid] and r['proxy_budget_integer']==max(scale//10**9,(3*expected_f[cid]+1)//2)
  u=q['source'];assert types[u]=='SOURCE' and caps[u]>0;value=initial[nodeclasses[u]];seen={u}
  for index,eid in enumerate(r['answer']['physical_edge_ids']):
   assert type(eid) is int and 0<=eid<len(us) and us[eid]==u;v=vs[eid];assert v not in seen and caps[v]>0
   if index<len(r['answer']['physical_edge_ids'])-1:assert types[v] not in ['SOURCE','SINK']
   if types[v]!='SINK':
    key=q['net_id'];edge=(u,eid);assert v not in parents[key] or parents[key][v]==edge;parents[key][v]=edge
   seen.add(v);value+=weights[eid];u=v
  assert u==q['sink'] and types[u]=='SINK' and value==r['answer']['delay']<=expected[cid] and expected_f[cid]<=value
  owners[q['net_id']].update(seen);independent_ledger.update(seen)
  if cid not in closure:assert r['answer']==old[cid]['answer']
  if mode=='raw_min':assert r['answer']==minimum[cid]['answer']
 ledger=Counter(n for nodes in owners.values() for n in nodes);assert frame['ledger']=={str(n):v for n,v in ledger.items()} and frame['independent_connection_ledger']=={str(n):v for n,v in independent_ledger.items()};overflow=sum(max(0,v-caps[n]) for n,v in ledger.items());assert overflow==frame['overflow_units'];assert not frame['eligible_for_legal_route_commit']
 events=json.loads((D/mode/'initializer_events.json').read_text());assert len(events)==len(dirty) and {e['net_id'] for e in events}==dirty
 retained=0
 if mode=='native_retained':
  for event in events:
   members={cid for cid,q in queries.items() if q['net_id']==event['net_id']};eligible=sorted(members-direct);assert event['attempted_retained_connection_ids']==eligible
   if event['whole_NET_fallback']:
    assert event['retained_connection_ids']==[]
    for cid in members:assert records[cid]['answer']==minimum[cid]['answer']
   else:
    assert event['retained_connection_ids']==eligible and event['repair_calls']==len(members&direct)
    for cid in eligible:assert records[cid]['answer']==old[cid]['answer']
    retained+=len(eligible)
 rows.append(dict(mode=mode,connections=len(records),whole_NETs=len(owners),overflow_units=overflow,retained_stable_siblings=retained,all_original_XML_fraction_paths_budgets_parents_ledgers_pass=True));print('AUDIT PASS',mode,overflow,retained,flush=True)
assert all(allrecords['raw_min'][cid]['budget_integer']==allrecords['native_retained'][cid]['budget_integer'] for cid in queries)
assert all(sha(p)==h for p,h in bindings.items())
with (D/'initial_independent_verification_v1.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,rows=rows,all115572V2budgets_matched=True,fresh_source_certificates_equal_bound_independent_XML_reference=len(fresh['certificates']),changed_endpoint_floors=len(direct),unchanged_endpoint_cached_floors_crosschecked_fresh=len(closure-direct),all_old_minima_new_dual_scope=False,feedback_on_arms_pending=True,seconds=time.perf_counter()-tick,scope='New initialization frames independently originalXML/Fraction validated. Overused sketches are not accepted legal routes. Matched V2heuristic budget law not STA guarantee; exposed MMC only, no full workflow or hardware gain.'),f,indent=2)
print('BOTH INITIALIZER AUDITS COMPLETE',flush=True)

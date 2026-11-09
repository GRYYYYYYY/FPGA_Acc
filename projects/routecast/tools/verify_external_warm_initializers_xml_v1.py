"""Independent original-XML warm path/budget/ledger audit. No native acceptance."""
import argparse,json,time,xml.etree.ElementTree as ET
from pathlib import Path
from array import array
from fractions import Fraction as F
from collections import defaultdict,Counter
from pre_route_endpoints import sha
p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path);a=p.parse_args()
D=a.directory.resolve();start=time.perf_counter();rp=D/'receipt.json';receipt=json.loads(rp.read_text())
assert receipt['status']=='WARM_PRODUCED_INDEPENDENT_AUDIT_PENDING'
assert all(sha(p)==h for p,h in receipt['bindings'].items())
frame=json.loads((D/'initial.json').read_text());scale=frame['scale'];assert scale==10**18
meta=json.loads(Path(receipt['endpoint']).read_text());graph=Path(meta['inputs']['graph']['path'])
assert sha(graph)==meta['graph_sha256']==frame['graph_sha256']
for entry in meta['inputs'].values():assert sha(entry['path'])==entry['sha256']
source_dir=Path(receipt['source_directory']);sp=source_dir/'independent_xml_verification_v1.json';source_proof=json.loads(sp.read_text())
assert source_proof['status']=='SOURCE_XML_FRACTION_PATH_BUDGET_LEDGER_AUDIT_PASS'
assert receipt['bindings'][str(sp)]==sha(sp)
assert all(sha(p)==h for p,h in source_proof['bindings'].items())
source=json.loads((source_dir/'initial.json').read_text());assert source['scale']==scale and source['graph_sha256']==meta['graph_sha256']
old={r['connection_id']:r for r in source['records']};assert len(old)==len(source['records'])
fp=Path(receipt['floor_proof']);proof=json.loads(fp.read_text());fl=fp.parent/'floors.jsonl'
assert proof['status']=='ALL_FRAME_RAW_FLOORS_ORIGIN_PROOFS_NEW_MINIMA_AND_CURRENT_XML_PATHS_VERIFIED' and proof['unreachable']==0
assert proof['graph_sha256']==meta['graph_sha256'] and proof['bindings'][str(fl)]==sha(fl)
floors={}
for line in fl.read_text().splitlines():
 row=json.loads(line);assert row['connection_id'] not in floors;floors[row['connection_id']]=row
queries={q['connection_id']:q for q in meta['connections']};records={r['connection_id']:r for r in frame['records']}
assert len(queries)==len(meta['connections'])==len(records)==len(frame['records']) and set(queries)==set(records)==set(old)==set(floors)
dirty=set()
for cid,q in queries.items():
 assert q['net_id']==old[cid]['net_id']
 if (q['source'],q['sink'])!=(old[cid]['source'],old[cid]['sink']):dirty.add(q['net_id'])
assert sorted(dirty)==receipt['dirty_nets']
mode=receipt['initializer_policy'];assert mode in ('raw_min','native_retained') and frame['initializer_policy']==mode
caps=array('I');types=[];nodeclasses=array('I');classes=[];lookup={};switches={};us=array('I');vs=array('I');ss=array('I');weights=array('Q');cost_cache={};stack=[]
print('EXTERNAL INDEPENDENT XML READ START',flush=True)
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

owners=defaultdict(set);parents=defaultdict(dict);independent=Counter();pairs={}
for cid,q in queries.items():
 record=records[cid];assert all(record[k]==v for k,v in q.items())
 f=floors[cid];assert all(f[k]==q[k] for k in ('net_id','source','sink'))
 floor=f['minimum_integer'];assert type(floor) is int and floor>=0
 proxy=max(scale//10**9,(3*floor+1)//2)
 same=(q['source'],q['sink'])==(old[cid]['source'],old[cid]['sink'])
 if same:assert floor==old[cid]['floor_integer']
 budget=max(proxy,old[cid]['answer']['delay']) if same else proxy
 assert record['floor_integer']==floor and record['proxy_budget_integer']==proxy and record['budget_integer']==budget
 if q['net_id'] not in dirty:assert record['answer']==old[cid]['answer']
 u=q['source'];assert type(u) is int and 0<=u<len(caps) and types[u]=='SOURCE' and caps[u]>0
 delay=initial[nodeclasses[u]];seen={u};edges=record['answer']['physical_edge_ids']
 for i,eid in enumerate(edges):
  assert type(eid) is int and 0<=eid<len(us) and us[eid]==u
  v=vs[eid];assert v not in seen and caps[v]>0
  if i<len(edges)-1:assert types[v] not in ('SOURCE','SINK')
  if types[v]!='SINK':
   incoming=(u,eid);pp=parents[q['net_id']];assert v not in pp or pp[v]==incoming;pp[v]=incoming
  seen.add(v);delay+=weights[eid];u=v
 assert u==q['sink'] and types[u]=='SINK' and record['answer']['status']=='FOUND'
 assert delay==record['answer']['delay'] and floor<=delay<=budget
 if mode=='raw_min' and q['net_id'] in dirty:assert delay==floor
 pair=(q['source'],q['sink']);assert pair not in pairs or pairs[pair]==floor;pairs[pair]=floor
 owners[q['net_id']].update(seen);independent.update(seen)
ledger=Counter(n for ns in owners.values() for n in ns)
assert frame['ledger']=={str(n):v for n,v in ledger.items()}
assert frame['independent_connection_ledger']=={str(n):v for n,v in independent.items()}
assert frame['overflow_units']==sum(max(0,v-caps[n]) for n,v in ledger.items())
assert frame['history']=={} and json.loads((D/'history.json').read_text())=={}
assert frame['epochs']=={str(net):int(net in dirty) for net in owners}
assert frame['completed_connections']==frame['required_connections']==len(records) and frame['eligible_for_legal_route_commit'] is False
assert frame['budget_policy']==receipt['native_anchored_budget_policy']=='NATIVE_ENDPOINT_ANCHORED_PROXY_V2'
assert json.loads((D/'floors.json').read_text())==[dict(source=s,sink=t,minimum_integer=v) for (s,t),v in sorted(pairs.items())]
events=json.loads((D/'initializer_events.json').read_text())
if mode=='raw_min':assert events==[]
else:
 assert len(events)==len(dirty) and {e['net_id'] for e in events}==dirty
 for event in events:
  net=event['net_id'];eligible=sorted(cid for cid,q in queries.items() if q['net_id']==net and (q['source'],q['sink'])==(old[cid]['source'],old[cid]['sink']))
  assert event['attempted_retained_connection_ids']==eligible
  assert event['retained_connection_ids']==([] if event['whole_NET_fallback'] else eligible)
  for cid in event['retained_connection_ids']:assert records[cid]['answer']==old[cid]['answer']
bindings={**receipt['bindings'],str(rp):sha(rp),str(Path(__file__).resolve()):sha(__file__)}
assert all(sha(p)==h for p,h in bindings.items())
result=dict(schema='NATIVE_ENDPOINT_ANCHORED_WARM_INPUT_V2',status='EXTERNAL_WARM_XML_PATHS_MATCHED_BUDGETS_LEDGER_AND_SOURCE_RETENTION_PASS',bindings=bindings,endpoint=receipt['endpoint'],dirty_nets=sorted(dirty),native_staged_state_independent_xml_pass=True,zero_initial_history=True,native_anchored_budget_policy='NATIVE_ENDPOINT_ANCHORED_PROXY_V2',connections=len(records),initializer_policy=mode,verification_seconds=time.perf_counter()-start,scope='Independent original XML/Fraction paths, parent/capacity accounting, matched budgets, epochs and source retention. Cross-NET overflow permitted as prediction. Floor minima inherited from bound certified input, no new shortest-distance proof. No native FULL or STA acceptance, quality or time gain.')
with (D/'verification.json').open('x') as f:json.dump(result,f,indent=2)
print('EXTERNAL_WARM_XML_AUDIT_PASS',mode,len(records),flush=True)

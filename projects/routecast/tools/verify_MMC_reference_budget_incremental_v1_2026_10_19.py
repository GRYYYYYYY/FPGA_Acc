"""Independent original-XML paths, reference budgets, insert journal and full/partial state."""
import pathlib,json,hashlib,struct,math,xml.etree.ElementTree as ET
from fractions import Fraction
from array import array
from collections import Counter,defaultdict
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_reference_budget_incremental_v1_2026-10-19'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 protocol=json.loads((O/'protocol.json').read_text());terminal=json.loads((O/'receipt.json').read_text());common=json.loads((O/'common_context.json').read_text());assert terminal['status']=='ALL3_FIXED_DIAGNOSTIC_UPDATE_PASSES_TERMINAL'
 for p,h in {**protocol['bindings'],**common['native_search_bindings']}.items():assert sha(pathlib.Path(p))==h
 assert sha(pathlib.Path(common['graph']))==common['graph_sha256']
 graph=pathlib.Path(common['graph']);caps=array('I');spans=array('I');kinds=[];us=array('I');vs=array('I');ss=array('I');weights=array('Q');switches={};stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes':
   assert int(e.get('id'))==len(caps);caps.append(int(e.get('capacity')));kinds.append(e.get('type'));loc=e.find('loc');kind=e.get('type');spans.append(int(loc.get('xhigh'))-int(loc.get('xlow'))+1 if kind=='CHANX' else (int(loc.get('yhigh'))-int(loc.get('ylow'))+1 if kind=='CHANY' else 0));t=e.find('timing');assert Fraction(t.get('R'))==Fraction(t.get('C'))==0
  elif e.tag=='switch' and parent=='switches':
   t=e.find('timing');assert e.get('type') in ['buffer','mux','tristate'] and Fraction(t.get('Cinternal','0'))==0;w=Fraction(t.get('Tdel','0'))*10**18;assert w.denominator==1;switches[int(e.get('id'))]=int(w)
  elif e.tag=='edge' and parent=='rr_edges':us.append(int(e.get('src_node')));vs.append(int(e.get('sink_node')));ss.append(int(e.get('switch_id')));weights.append(switches[int(e.get('switch_id'))])
  if (e.tag,parent) in [('node','rr_nodes'),('switch','switches'),('edge','rr_edges')]:stack[-2].remove(e);e.clear()
  stack.pop()
 assert len(us)==8097539 and len(caps)==904438;assert common['nonbinding_added_span_bound_exclusive']==sum(spans[v] for v in range(len(caps)) if caps[v]>0)+1
 S=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18/initial.json';old={q['connection_id']:q for q in json.loads(S.read_text())['records']};T=R/'experiments/mmc_reference_setup_slack_export_v1_2026-10-19/model_connection_reference_slacks.json';slacks={q['connection_id']:q for q in json.loads(T.read_text())};results=[];bindings={str(p):sha(p) for p in [O/'protocol.json',O/'receipt.json',O/'common_context.json',S,T,graph,pathlib.Path(__file__).resolve()]}
 def walk(q,ids):
  u=q['source'];seen={u};value=0;edges=[];assert kinds[u]=='SOURCE' and caps[u]>0
  for eid in ids:
   assert type(eid) is int and 0<=eid<len(us);a,b,w=us[eid],vs[eid],weights[eid];assert a==u and b not in seen and caps[b]>0 and kinds[a]!='SINK' and kinds[b]!='SOURCE';seen.add(b);edges.append((b,a,int(ss[eid])));value+=w;u=b
  assert u==q['sink'] and kinds[u]=='SINK';return seen,value,edges
 for plan in protocol['cases']:
  case=plan['case'];d=O/case;targetmeta=json.loads(pathlib.Path(plan['endpoint']).read_text());assert targetmeta['graph_sha256']==common['graph_sha256'];queries={q['connection_id']:q for q in targetmeta['connections']};assert set(queries)==set(old);changed=sorted((cid for cid,q in queries.items() if (q['source'],q['sink'])!=(old[cid]['source'],old[cid]['sink'])),key=lambda cid:(queries[cid]['net_id'],cid));assert changed==plan['changed_CIDs'];retained=set(old)-set(changed);state={};parents=defaultdict(dict);refs=defaultdict(Counter);occ=Counter();budgetmap={};events=[json.loads(line) for line in (d/'events.jsonl').read_text().splitlines()];model=json.loads((d/'model.json').read_text());mr={q['connection_id']:q for q in model['records']};assert len(mr)==len(model['records']);outcome=json.loads((d/'receipt.json').read_text())
  def add(cid,ids,budget):
   q=queries[cid];net=q['net_id'];seen,value,edges=walk(q,ids);assert value<=budget
   for v in seen:assert occ[v]-int(v in refs[net])<caps[v]
   for v,u,s in edges:
    if v in parents[net]:assert parents[net][v]==(u,s)
   for v in seen:
    if refs[net][v]==0:occ[v]+=1
    refs[net][v]+=1
   for v,u,s in edges:parents[net][v]=(u,s)
   state[cid]=(tuple(ids),value);budgetmap[cid]=budget;return seen,value
  for cid in sorted(retained):
   q=queries[cid];assert all(q[k]==old[cid][k] for k in ['net_id','source','sink']);add(cid,old[cid]['answer']['physical_edge_ids'],old[cid]['answer']['delay']);assert mr[cid]['mode']=='RETAINED_NATIVE' and mr[cid]['answer']==old[cid]['answer']
  initial_span=sum(spans[v] for ns in refs.values() for v in ns);assert initial_span==outcome['initial_retained_NET_unique_CHAN_span'];assert [e['connection_id'] for e in events]==changed;inserted=0
  for e in events:
   cid=e['connection_id'];q=queries[cid];net=q['net_id'];row=slacks[cid];assert e['reference_slack_float32_bits']==row['setup_slack_float32_bits'];raw=struct.unpack('<f',struct.pack('<I',row['setup_slack_float32_bits']))[0];valid=math.isfinite(raw) and not row['clock_sink'];fraction=Fraction.from_float(max(raw,0))*10**18 if valid else Fraction(0);credit=fraction.numerator//fraction.denominator;budget=old[cid]['answer']['delay']+credit;assert e['reference_credit']==credit and e['diagnostic_RC_budget']==budget
   if e['committed']:
    assert e['status']=='FOUND' and e['admission_error'] is None;seen,value,edges=walk(q,e['physical_edge_ids']);assert value==e['delay']<=budget;cost=sum(spans[v] for v in seen if v not in refs[net]);assert cost==e['cost'];add(cid,e['physical_edge_ids'],budget);inserted+=1
   else:
    assert cid not in state
    if e['status']=='BLOCKED_SOURCE_CAPACITY':assert occ[q['source']]-int(q['source'] in refs[net])>=caps[q['source']]
    elif e['status']=='UNSUPPORTED_REFERENCE_SLACK':assert not valid
    else:assert e['status'] in ['LABEL_LIMIT','NO_STRICT_IMPROVEMENT'] and e['physical_edge_ids'] is None
   if 'labels_created' in e:assert e['labels_created']<=10000
  pending=sorted(set(queries)-set(state));assert pending==model['pending_connection_ids']==outcome['pending_connection_ids'];assert len(state)==model['completed_connections'] and model['required_connections']==115572 and set(state)==set(mr)
  # Fresh final reconstruction does not use the journal's incremental owner counts.
  unions=defaultdict(set);freshparents=defaultdict(dict)
  for cid,r in mr.items():
   assert all(r[k]==queries[cid][k] for k in ['net_id','source','sink']);assert r['answer']['status']=='FOUND';assert (tuple(r['answer']['physical_edge_ids']),r['answer']['delay'])==state[cid] and r['budget_integer']==budgetmap[cid];seen,value,edges=walk(r,r['answer']['physical_edge_ids']);assert value==r['answer']['delay']<=budgetmap[cid];n=r['net_id'];unions[n].update(seen)
   for v,u,s in edges:
    if v in freshparents[n]:assert freshparents[n][v]==(u,s)
    freshparents[n][v]=(u,s)
  final=Counter(v for ns in unions.values() for v in ns);assert final==occ and {str(v):n for v,n in final.items()}==model['ledger'] and all(n<=caps[v] for v,n in final.items());span=sum(spans[v] for ns in unions.values() for v in ns);assert span==outcome['final_present_NET_unique_CHAN_span'];complete=not pending;assert model['eligible_for_native_serialization']==complete and not model['eligible_for_live_route_commit'] and outcome['quality_comparison_eligible']==complete
  row=dict(case=case,retained=len(retained),rebuilt=inserted,completed=len(state),pending_CIDs=pending,capacity_overflow=0,all_present_paths_XML_reference_budget_and_single_parent_pass=True,all_event_insertions_exact_final_owner_ledger=True,full_state_complete=complete,full_quality_comparison_eligible=complete,present_unique_NET_CHAN_span=span);results.append(row);print('INDEPENDENT UPDATE PASS',row,flush=True)
  for p in [d/'model.json',d/'events.jsonl',d/'receipt.json',pathlib.Path(plan['endpoint'])]:bindings[str(p)]=sha(p)
 with (O/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL3_ACTUAL_LAYOUT_RETAINED_AND_REBUILT_PATHS_REFERENCE_BUDGETS_TRANSACTIONS_AUDITED',cases=results,bindings=bindings,scope='All present paths and all frozen update events verified in original graph, including partial cases. Reference-slack budgets are diagnostic only, not joint setup timing proof. Complete case still requires native FULL/STA/canonical/quality; partial cases never become zero-demand full predictions.'),f,indent=2)
if __name__=='__main__':main()

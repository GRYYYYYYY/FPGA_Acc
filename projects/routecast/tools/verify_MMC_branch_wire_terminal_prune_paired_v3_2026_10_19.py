"""Original80 input parity and independent full-XML conditional proposal audits."""
import pathlib,json,hashlib,xml.etree.ElementTree as ET
from fractions import Fraction
from array import array
from collections import Counter,defaultdict
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_branch_wire_terminal_prune_paired_v3_2026-10-19';A=R/'experiments/mmc_prior_budget_branch_wire_pilot_v1_2026-10-19'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 protocol=json.loads((O/'protocol.json').read_text());result=json.loads((O/'results.json').read_text())
 for p,h in result['bindings'].items():assert sha(pathlib.Path(p))==h
 oldproof=A/'independent_verification_v1.json';v=json.loads(oldproof.read_text());assert v['status']=='FULL115572_CONNECTION_XML_RC_CAPACITY_AND_ALL80_RESOURCE_TRANSACTIONS_PASS';assert sha(A/'events.jsonl')==v['bindings'][str(A/'events.jsonl')];old=[json.loads(line) for line in (A/'events.jsonl').read_text().splitlines()];new=[json.loads(line) for line in (O/'events.jsonl').read_text().splitlines()];assert len(old)==len(new)==80
 ignore=['seconds','pruned_answer','control_query_seconds','pruned_query_seconds']
 for a,b in zip(old,new):assert {k:v for k,v in a.items() if k not in ignore}=={k:v for k,v in b.items() if k not in ignore}
 for name in ['final_unique_NET_occupancy.json']+[f'net_{n}_tree.json' for n in protocol['NETs']]:assert json.loads((O/name).read_text())==json.loads((A/name).read_text())
 first_commit=min(e['ordinal'] for e in old if e['committed']);assert all(e['ordinal']<=first_commit for e in new if e['pruned_answer'] is not None)
 protocol['bindings']=result['bindings']
 graph=next(pathlib.Path(p) for p in protocol['bindings'] if p.endswith('rr_graph.xml'));caps=array('I');spans=array('I');kinds=[];us=array('I');vs=array('I');ss=array('I');weights=array('Q');switches={};stack=[]
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
 assert len(us)==8097539 and len(caps)==904438;source=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18/initial.json';frame=json.loads(source.read_text());records={q['connection_id']:q for q in frame['records']};global_count={int(n):c for n,c in frame['ledger'].items()};refs=defaultdict(Counter);parents=defaultdict(dict);parent_uses=defaultdict(Counter);pathnodes={};nets=set(protocol['NETs'])
 def audit(q,ids):
  u=q['source'];seen={u};cost=0;arcs=[];assert kinds[u]=='SOURCE' and caps[u]>0
  for eid in ids:
   assert type(eid) is int and 0<=eid<len(us);a,b,w=us[eid],vs[eid],weights[eid];assert a==u and b not in seen and caps[b]>0 and kinds[a]!='SINK' and kinds[b]!='SOURCE';seen.add(b);arcs.append((b,a,int(ss[eid])));u=b;cost+=w
  assert u==q['sink'] and kinds[u]=='SINK';return seen,cost,arcs
 for cid,q in records.items():
  n=q['net_id']
  if n not in nets:continue
  seen,cost,arcs=audit(q,q['answer']['physical_edge_ids']);assert cost==q['answer']['delay'];refs[n].update(seen);pathnodes[cid]=seen
  for child,parent,switch in arcs:
   if child in parents[n]:assert parents[n][child]==(parent,switch)
   parents[n][child]=(parent,switch);parent_uses[n][child]+=1
 rows=[];transitions=Counter();control_seconds=0;pruned_seconds=0
 for event in new:
  proposal=event['pruned_answer']
  if proposal is None:continue
  q=records[event['connection_id']];n=q['net_id'];cid=q['connection_id'];oldnodes=pathnodes[cid];kept={node for node,count in refs[n].items() if count>int(node in oldnodes)};released=sum(spans[node] for node in oldnodes-kept);assert released==event['released_unique_span'];transitions[(event['status'],proposal['status'])]+=1;assert proposal['labels_created']<=10000;control_seconds+=event['control_query_seconds'];pruned_seconds+=event['pruned_query_seconds']
  if proposal['status']=='FOUND':
   seen,cost,arcs=audit(q,proposal['physical_edge_ids']);assert cost==proposal['delay']<=q['answer']['delay'];assert sum(spans[node] for node in seen-kept)==proposal['cost']<released
   for node in seen:assert global_count.get(node,0)-int(node in refs[n])<caps[node]
   for child,parent,switch in arcs:
    if parent_uses[n][child]>int(child in oldnodes and child!=q['source']):assert parents[n][child]==(parent,switch)
  else:assert proposal['status'] in ['NO_STRICT_IMPROVEMENT','LABEL_LIMIT'] and proposal['physical_edge_ids'] is None
  if event['status']=='FOUND':assert proposal['status']=='FOUND' and [event['cost'],event['delay']]==[proposal['cost'],proposal['delay']]
  rows.append(dict(connection_id=cid,original_status=event['status'],pruned_status=proposal['status'],original_labels=event['labels_created'],pruned_labels=proposal['labels_created'],static_terminal_flag_bytes=proposal['static_terminal_flag_bytes'],terminal_neighbor_tests=proposal['terminal_neighbor_tests'],target_pruned_forward_edges=proposal['terminal_pruned_edges'],proposal_cost=proposal.get('cost'),proposal_RC=proposal.get('delay')))
 assert len(rows)==22;bindings={str(p):sha(p) for p in [oldproof,A/'events.jsonl',O/'protocol.json',O/'results.json',O/'events.jsonl',source,graph,pathlib.Path(__file__).resolve()]}
 summary=dict(transitions=[dict(original=a,pruned=b,queries=c) for (a,b),c in sorted(transitions.items())],original_labels=sum(row['original_labels'] for row in rows),pruned_labels=sum(row['pruned_labels'] for row in rows),control_query_seconds=control_seconds,pruned_query_seconds_including_terminal_predicates=pruned_seconds,original_label_limit_queries=sum(r['original_status']=='LABEL_LIMIT' for r in rows),remaining_label_limit_queries=sum(r['pruned_status']=='LABEL_LIMIT' for r in rows),conditional_proposals_independently_XML_and_RC_and_resource_and_fixed_parent_capacity_verified=sum(r['pruned_status']=='FOUND' for r in rows))
 with (O/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL80_CONTROL_PARITY_AND_ALL22_IDENTICAL_CONTEXT_TARGET_PRUNED_PROPOSALS_AUDITED',summary=summary,rows=rows,bindings=bindings,scope='Sidecar candidates independently checked against original fixed contexts; they were not committed. Timing includes each wrapper query preparation and terminal predicates, excludes graph/setup/verification. No new full policy, native utility, generalization or end-to-end speedup.'),f,indent=2)
 print(json.dumps(summary),flush=True)
if __name__=='__main__':main()

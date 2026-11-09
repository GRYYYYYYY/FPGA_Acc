"""Independent all-subset tree compatibility and complete old-source state audit."""
import pathlib,json,hashlib,itertools,xml.etree.ElementTree as ET
from fractions import Fraction
from array import array
from collections import defaultdict,Counter
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_branch_proposal_joint_bank_v1_2026-10-19'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 protocol=json.loads((O/'protocol.json').read_text());result=json.loads((O/'results.json').read_text())
 for p,h in protocol['bindings'].items():assert sha(pathlib.Path(p))==h
 graph=next(pathlib.Path(p) for p in protocol['bindings'] if p.endswith('rr_graph.xml'));caps=array('I');spans=array('I');kinds=[];us=array('I');vs=array('I');weights=array('Q');switches={};stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes':
   assert int(e.get('id'))==len(caps);caps.append(int(e.get('capacity')));kinds.append(e.get('type'));loc=e.find('loc');kind=e.get('type');spans.append(int(loc.get('xhigh'))-int(loc.get('xlow'))+1 if kind=='CHANX' else (int(loc.get('yhigh'))-int(loc.get('ylow'))+1 if kind=='CHANY' else 0));t=e.find('timing');assert Fraction(t.get('R'))==Fraction(t.get('C'))==0
  elif e.tag=='switch' and parent=='switches':
   t=e.find('timing');assert e.get('type') in ['buffer','mux','tristate'] and Fraction(t.get('Cinternal','0'))==0;w=Fraction(t.get('Tdel','0'))*10**18;assert w.denominator==1;switches[int(e.get('id'))]=int(w)
  elif e.tag=='edge' and parent=='rr_edges':us.append(int(e.get('src_node')));vs.append(int(e.get('sink_node')));weights.append(switches[int(e.get('switch_id'))])
  if (e.tag,parent) in [('node','rr_nodes'),('switch','switches'),('edge','rr_edges')]:stack[-2].remove(e);e.clear()
  stack.pop()
 assert len(us)==8097539 and len(caps)==904438;source=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18/initial.json';frame=json.loads(source.read_text());records={q['connection_id']:q for q in frame['records']};P=R/'experiments/mmc_branch_wire_target_prune_paired_v2_2026-10-19';events=[json.loads(e) for e in (P/'events.jsonl').read_text().splitlines()];proposals={e['connection_id']:e['pruned_answer']['physical_edge_ids'] for e in events if e['pruned_answer'] and e['pruned_answer']['status']=='FOUND'};assert sorted(proposals)==protocol['proposal_CIDs'];nets=protocol['NETs'];group=defaultdict(list)
 for q in records.values():
  if q['net_id'] in nets:group[q['net_id']].append(q)
 def path_audit(q,ids):
  u=q['source'];seen={u};cost=0;arcs=[];assert kinds[u]=='SOURCE' and caps[u]>0
  for eid in ids:
   assert type(eid) is int and 0<=eid<len(us);a,b,w=us[eid],vs[eid],weights[eid];assert a==u and b not in seen and caps[b]>0 and kinds[a]!='SINK' and kinds[b]!='SOURCE';seen.add(b);arcs.append((b,a,eid));cost+=w;u=b
  assert u==q['sink'] and kinds[u]=='SINK' and cost<=q['answer']['delay'];return seen,cost,arcs
 expected={};native_unions={};invalid=[];A=R/'experiments/mmc_prior_native_budget_bank_v1_2026-10-19';bindings={str(p):sha(p) for p in [O/'protocol.json',O/'results.json',source,graph,pathlib.Path(__file__).resolve()]}
 for net in nets:
  cids=sorted(cid for cid in proposals if records[cid]['net_id']==net);base=json.loads((A/f'net_{net}_prior_native.json').read_text());expected[net]={};ci=0
  for flags in itertools.product([False,True],repeat=len(cids)):
   changes={cid:proposals[cid] for cid,f in zip(cids,flags) if f};nodes=set();parents={};costs={};paths={};valid=True
   for q in group[net]:
    ids=changes.get(q['connection_id'],q['answer']['physical_edge_ids']);seen,cost,arcs=path_audit(q,ids);nodes.update(seen);costs[str(q['sink'])]=cost;paths[str(q['sink'])]=ids
    for child,parent,eid in arcs:
     if child in parents and parents[child]!=(parent,eid):valid=False
     parents[child]=(parent,eid)
   if not valid:invalid.append((net,sorted(changes)));continue
   p=O/f'net_{net}_candidate_{ci}.json';x=json.loads(p.read_text());excess=sum(v-base['sink_floors'][sink] for sink,v in costs.items());wire=sum(spans[n] for n in nodes);assert x['proposal_CIDs']==sorted(changes) and x['paths']==paths and x['sink_costs']==costs and x['unique_nodes']==sorted(nodes) and x['excess']==excess and x['CHAN_span']==wire
   expected[net][frozenset(changes)]=dict(index=ci,nodes=nodes,objective=(wire,excess),record=x);bindings[str(p)]=sha(p)
   if not changes:native_unions[net]=nodes
   ci+=1
  assert ci==result['bank_sizes'][str(net)];print('INDEPENDENT BANK',net,ci,flush=True)
 assert sorted(invalid)==sorted((r['net_id'],r['proposal_CIDs']) for r in result['rejected_same_NET_subsets']);fixed=Counter({int(n):c for n,c in frame['ledger'].items()})
 for ns in native_unions.values():fixed.subtract(ns)
 assert all(v>=0 for v in fixed.values());masks=[];feasible=[];proposal_ids=sorted(proposals)
 for flags in itertools.product([False,True],repeat=4):
  chosen=frozenset(cid for cid,f in zip(proposal_ids,flags) if f);own=Counter();objective=[0,0];compatible=True
  for net in nets:
   local=frozenset(cid for cid in chosen if records[cid]['net_id']==net)
   if local not in expected[net]:compatible=False;break
   c=expected[net][local];own.update(c['nodes']);objective=[a+b for a,b in zip(objective,c['objective'])]
  if not compatible:masks.append(dict(chosen=sorted(chosen),status='SAME_NET_PARENT_CONFLICT'));continue
  bad=sorted(n for n,c in own.items() if c+fixed[n]>caps[n]);masks.append(dict(chosen=sorted(chosen),status='CAPACITY_CONFLICT' if bad else 'FEASIBLE',objective=objective,capacity_witness=bad[0] if bad else None))
  if not bad:feasible.append((tuple(objective),chosen))
 assert feasible;minimum=min(v for v,_ in feasible);assert list(minimum)==result['answer']['objective'];chosen=frozenset(result['selected_proposal_CIDs']);assert (minimum,chosen) in feasible
 patch=json.loads((O/'selected_connection_patch.json').read_text());assert set(map(int,patch))==chosen
 for cid in chosen:assert patch[str(cid)]==dict(net_id=records[cid]['net_id'],source=records[cid]['source'],sink=records[cid]['sink'],physical_edge_ids=proposals[cid],RC_budget=records[cid]['answer']['delay'])
 # Rebuild every connection, parent relation and NET union in the full source state.
 unions=defaultdict(set);parents=defaultdict(dict);prior_RC=0;new_RC=0;improved=0
 for cid,q in records.items():
  ids=proposals[cid] if cid in chosen else q['answer']['physical_edge_ids'];seen,cost,arcs=path_audit(q,ids);unions[q['net_id']].update(seen);prior_RC+=q['answer']['delay'];new_RC+=cost;improved+=cost<q['answer']['delay']
  for child,parent,eid in arcs:
   if child in parents[q['net_id']]:assert parents[q['net_id']][child]==(parent,eid)
   parents[q['net_id']][child]=(parent,eid)
 full=Counter(v for ns in unions.values() for v in ns);assert {str(n):c for n,c in full.items()}==json.loads((O/'selected_full_prior_unique_NET_occupancy.json').read_text());assert len(unions)==55300 and len(records)==115572 and all(c<=caps[n] for n,c in full.items())
 before_span=sum(spans[int(n)]*c for n,c in frame['ledger'].items());after_span=sum(spans[n]*c for n,c in full.items())
 for net in nets:
  sel=json.loads((O/f'net_{net}_selected.json').read_text());local=frozenset(cid for cid in chosen if records[cid]['net_id']==net);assert sel==expected[net][local]['record'] and sel['index']==result['answer']['selection'][str(net)]
 with (O/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL16_PROPOSAL_SUBSETS_AND_FULL115572_CONNECTION_RC_CAPACITY_STATE_VERIFIED',all_masks=masks,feasible_masks=len(feasible),selected_CIDs=sorted(chosen),selected_objective=minimum,full_NETs=len(unions),full_connections=len(records),strictly_RC_improved_connections=improved,prior_full_sum_sink_RC=prior_RC,new_full_sum_sink_RC=new_RC,prior_full_unique_NET_CHAN_span=before_span,new_full_unique_NET_CHAN_span=after_span,bindings={**bindings,str(O/'selected_connection_patch.json'):sha(O/'selected_connection_patch.json'),str(O/'selected_full_prior_unique_NET_occupancy.json'):sha(O/'selected_full_prior_unique_NET_occupancy.json')},scope='Full old-source physical context, finite four proposals from fixed80 pilot. No new-placement completeness, native FULL/STA acceptance, unseen-family, original predictor-quality pass or end-to-end gain.'),f,indent=2)
 print('ALL16 AND FULL SOURCE PASS',sorted(chosen),before_span,after_span,'RC improved',improved,flush=True)
if __name__=='__main__':main()

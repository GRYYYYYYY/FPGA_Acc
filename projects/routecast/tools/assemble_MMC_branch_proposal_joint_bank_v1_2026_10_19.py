"""Complete NET trees for every subset of the four admitted conditional proposals."""
import pathlib,json,hashlib,itertools,time,xml.etree.ElementTree as ET
from collections import defaultdict,Counter
from MMC_zero_node_RC_shared_CSR_v1 import load
from coupled_NET_tree_candidates_csr_v2 import CSRIndex,tree_candidate
from coupled_NET_tree_resource_select_v2 import select
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_branch_proposal_joint_bank_v1_2026-10-19'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def main():
 O.mkdir(exist_ok=False);P=R/'experiments/mmc_branch_wire_target_prune_paired_v2_2026-10-19';proof=P/'independent_verification_v1.json';pv=json.loads(proof.read_text());assert pv['status']=='ALL80_CONTROL_PARITY_AND_ALL22_IDENTICAL_CONTEXT_TARGET_PRUNED_PROPOSALS_AUDITED';events=P/'events.jsonl';assert sha(events)==pv['bindings'][str(events)];proposals={e['connection_id']:e['pruned_answer']['physical_edge_ids'] for e in map(json.loads,events.read_text().splitlines()) if e['pruned_answer'] and e['pruned_answer']['status']=='FOUND'};assert len(proposals)==4
 S=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18/initial.json';frame=json.loads(S.read_text());records={r['connection_id']:r for r in frame['records']};A=R/'experiments/mmc_prior_native_budget_bank_v1_2026-10-19';ap=A/'independent_verification_v1.json';av=json.loads(ap.read_text());fixedp=A/'fixed_prior_other_NET_occupancy.json';assert sha(fixedp)==av['bindings'][str(fixedp)];fixed={int(v):c for v,c in json.loads(fixedp.read_text()).items()};graph=next(pathlib.Path(p) for p in pv['bindings'] if p.endswith('rr_graph.xml'));nets=[1395,1400,1404,1754,2925];group=defaultdict(list)
 for r in records.values():
  if r['net_id'] in nets:group[r['net_id']].append(r)
 bindings={str(p):sha(p) for p in [proof,events,S,ap,fixedp,graph,pathlib.Path(__file__).resolve(),R/'tools/coupled_NET_tree_candidates_csr_v2.py',R/'tools/coupled_NET_tree_resource_select_v2.py']}
 for net in nets:
  p=A/f'net_{net}_prior_native.json';assert sha(p)==av['bindings'][str(p)];bindings[str(p)]=sha(p)
 write(O/'protocol.json',dict(bindings=bindings,proposal_CIDs=sorted(proposals),NETs=nets,policy='All2^4 proposal subsets, including both same-NET substitutions and all cross-NET combinations. RC bound equals each connection exact previous native actual RC. Complete-tree one-parent and full prior capacity mandatory. Primary unique-NET CHAN span; secondary sum sink RC excess. No candidate/order/budget/label tuning.',scope='Known old-source55300-NET physical state, five unchanged NETs. Sparse candidate patch only, no live route installation, new-placement route, native FULL/STA or predictor-quality gain.'))
 start=time.perf_counter();offsets,dest,cost,caps,kinds,graphseconds=load(graph);index=CSRIndex(offsets,dest,cost,caps,kinds);spans={};stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   kind=e.get('type')
   if kind in ['CHANX','CHANY']:
    loc=e.find('loc');axis='x' if kind=='CHANX' else 'y';spans[int(e.get('id'))]=int(loc.get(axis+'high'))-int(loc.get(axis+'low'))+1
   stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 banks={};metadata={};rejected=[]
 for net in nets:
  q=group[net];source=q[0]['source'];base=json.loads((A/f'net_{net}_prior_native.json').read_text());floor={int(s):v for s,v in base['sink_floors'].items()};budget={r['sink']:r['answer']['delay'] for r in q};assert len(budget)==len(q);cids=sorted(cid for cid in proposals if records[cid]['net_id']==net);banks[net]=[];metadata[net]=[]
  for flags in itertools.product([False,True],repeat=len(cids)):
   changes={cid:proposals[cid] for cid,f in zip(cids,flags) if f};paths={r['sink']:changes.get(r['connection_id'],r['answer']['physical_edge_ids']) for r in q}
   try:c=tree_candidate(index,source,paths,floor,budget)
   except ValueError as e:rejected.append(dict(net_id=net,proposal_CIDs=sorted(changes),reason=str(e)));continue
   ci=len(banks[net]);banks[net].append(c);record=dict(net_id=net,index=ci,source=source,proposal_CIDs=sorted(changes),paths=paths,sink_costs=c['sink_costs'],unique_nodes=sorted(c['nodes']),excess=c['excess'],CHAN_span=sum(spans.get(n,0) for n in c['nodes']));metadata[net].append(record);write(O/f'net_{net}_candidate_{ci}.json',record)
  print('BANK',net,len(banks[net]),flush=True)
 answer=select(banks,index.capacities,spans,fixed,max_states=100000);assert answer['status']=='OPTIMAL_WITHIN_CANDIDATES';chosen=[];occupancy=Counter(fixed)
 for net,ci in answer['selection'].items():chosen.extend(metadata[net][ci]['proposal_CIDs']);occupancy.update(banks[net][ci]['nodes']);write(O/f'net_{net}_selected.json',metadata[net][ci])
 assert all(c<=caps[n] for n,c in occupancy.items());write(O/'selected_connection_patch.json',{cid:dict(net_id=records[cid]['net_id'],source=records[cid]['source'],sink=records[cid]['sink'],physical_edge_ids=proposals[cid],RC_budget=records[cid]['answer']['delay']) for cid in sorted(chosen)});write(O/'selected_full_prior_unique_NET_occupancy.json',dict(occupancy));write(O/'results.json',dict(status='ALL_CONDITIONAL_BRANCH_SUBSETS_COMPLETE_TREE_BANK_SELECTED',bank_sizes={net:len(b) for net,b in banks.items()},rejected_same_NET_subsets=rejected,answer=answer,selected_proposal_CIDs=sorted(chosen),graph_load_seconds=graphseconds,construction_and_selection_seconds=time.perf_counter()-start,independent_all16_and_full_state_audit_pending=True));print(answer,'chosen',chosen,flush=True)
if __name__=='__main__':main()
